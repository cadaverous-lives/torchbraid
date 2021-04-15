#@HEADER
# ************************************************************************
# 
#                        Torchbraid v. 0.1
# 
# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC 
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S. 
# Government retains certain rights in this software.
# 
# Torchbraid is licensed under 3-clause BSD terms of use:
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 
# 3. Neither the name National Technology & Engineering Solutions of Sandia, 
# LLC nor the names of the contributors may be used to endorse or promote 
# products derived from this software without specific prior written permission.
# 
# Questions? Contact Eric C. Cyr (eccyr@sandia.gov)
# 
# ************************************************************************
#@HEADER

# cython: profile=True
# cython: linetrace=True

import torch
import traceback
import numpy as np

from braid_vector import BraidVector

import torchbraid_app as parent
import utils

import sys

from mpi4py import MPI

class ForwardBraidApp(parent.BraidApp):

  def __init__(self,comm,RNN_models,local_num_steps,hidden_size,num_layers,Tf,max_levels,max_iters,timer_manager,abs_tol):
    parent.BraidApp.__init__(self,'RNN',comm,local_num_steps,Tf,max_levels,max_iters,spatial_ref_pair=None,require_storage=True,abs_tol=abs_tol)

    self.hidden_size = hidden_size
    self.num_layers = num_layers

    self.RNN_models = RNN_models

    comm          = self.getMPIComm()
    my_rank       = self.getMPIComm().Get_rank()
    num_ranks     = self.getMPIComm().Get_size()

    # build up the core
    self.py_core = self.initCore()

    # force evaluation of gradients at end of up-cycle
    self.finalRelax()

    self.timer_manager = timer_manager
    self.use_deriv = False

    self.user_dt_ratio = self._dt_ratio_

    self.seq_shapes = None
    self.backpropped = dict()

    # parameters for the implicit coarse grid
    self.implicit_coarse_grid = False
    self.implicit_level = 1
    self.coarse_iters = 1
  # end __init__

  def _dt_ratio_(self,level,tstart,tstop,fine_dt): 
    return np.sqrt(np.sqrt((tstop-tstart)/fine_dt))

  def setDtRatio(self,user_dt_ratio):
    self.user_dt_ratio = user_dt_ratio

  def setImplicitCoarseGrid(self,enable=True):
    self.implicit_coarse_grid = enable

  def dt_ratio(self,level,tstart,tstop):
    return self.user_dt_ratio(level,tstart,tstop,self.dt)
  # end dt_ratio

  def getTensorShapes(self):
    return list(self.shape0)+self.seq_shapes

  def getSequenceVector(self,t,tf,level):
    index = self.getLocalTimeStepIndex(t,tf,level)
    if index<0: 
      pre_str = "\n{}: WARNING: getSequenceVector index negative at {}: {}\n".format(self.my_rank,t,index)
      stack_str = utils.stack_string('{}: |- '.format(self.my_rank))
      print(pre_str+stack_str)
 
    if index<self.x.shape[1]:
      value = self.x[:,index,:]
    else:
      # this is a sentinnel
      value = self.x[:,0,:].detach().clone()
      
    return value

  def clearTempLayerWeights(self):
    layer = self.temp_layer

    for dest_p in list(layer.parameters()):
      dest_p.data = torch.empty(())
  # end setLayerWeights

  def setLayerWeights(self,t,tf,level,weights):
    layer = self.getLayer(t,tf,level)

    with torch.no_grad():
      for dest_p,src_w in zip(list(layer.parameters()),weights):
        dest_p.data = src_w
  # end setLayerWeights

  def initializeVector(self,t,x):
    if t!=0.0: # don't change the initial condition
      for ten in x.tensors():
        ten[:] = 0.0
    seq_x = self.getSequenceVector(t,None,level=0)
    x.addWeightTensors((seq_x,))

  def run(self,x,h_c):
    num_ranks     = self.mpi_comm.Get_size()
    my_rank       = self.mpi_comm.Get_rank()
    comm = self.mpi_comm

    assert(x.shape[1]==self.local_num_steps)

    self.x = x
    self.seq_shapes = [x[:,0,:].shape]

    with self.timer("run:precomm"):
      recv_request = None
      if my_rank<num_ranks-1:
        neighbor_x = torch.zeros(x[:,0,:].shape)
        recv_request = comm.Irecv(neighbor_x.numpy(),source=my_rank+1,tag=22)

      # send deta vector to the left
      send_request = None
      if my_rank>0:
        send_request = comm.Isend(np.ascontiguousarray(self.x[:,0,:].numpy()),dest=my_rank-1,tag=22)

      if recv_request:
        recv_request.Wait()
        self.x = torch.cat((self.x,neighbor_x.unsqueeze(1)), 1)

      if send_request:
        send_request.Wait()
    # end wit htimer

    y = self.runBraid(h_c)

    with self.timer("run:postcomm"):
      y = comm.bcast(y,root=num_ranks-1)

    # y is a tuple with the final h,c components
    return y
  # end forward

  def timer(self,name):
    return self.timer_manager.timer("ForWD::"+name)

  def computeStep(self,level,tstart,tstop,x,u):
    """
    Propagate the RNN for a single time step, given
    data input x, and hidden state u. Output hidden state
    y.
    """

    dt = tstart-tstop

    if level<self.implicit_level:
      return self.RNN_models(x,*u)
    elif self.implicit_coarse_grid:
      # this introduces stability but things are not always converging...

      guess = u 

      for itr in range(self.coarse_iters):
        dy = self.RNN_models(x,*guess)

        # do an implicit coarse grid
        y = len(dy)*[None]
        for i in range(len(dy)):
          y[i] = (u[i] + dt*dy[i])/(1.0+dt)

        guess = y
      # end for itr
    else:
      dt_ratio = self.dt_ratio(level,tstart,tstop)

      y = self.RNN_models(x,*u)
      y = list(y)
      for i in range(len(y)):
        y[i] = (1.0-dt_ratio)*u[i]+dt_ratio*y[i]

    return y

  def eval(self,g0,tstart,tstop,level,done):
    """
    Method called by "my_step" in braid. This is
    required to propagate from tstart to tstop, with the initial
    condition x. The level is defined by braid
    """

    with self.timer("eval"):
      # there are two paths by which eval is called:
      #  1. x is a BraidVector: my step has called this method
      #  2. x is a torch tensor: called internally (probably at the behest
      #                          of the adjoint)
  
      seq_x = g0.weightTensors()[0]
  
      # don't need derivatives or anything, just compute
      if not done or level>0:
        u = g0.tensors()
        with torch.no_grad():
          y = self.computeStep(level,tstart,tstop,seq_x,u)

      else:
        # setup the solution vector for derivatives
        u = tuple([t.detach() for t in g0.tensors()])
        for t in u:
          t.requires_grad = True

        with torch.enable_grad():
          y = self.computeStep(level,tstart,tstop,seq_x,u)

        # store the fine level solution for reuse later in backprop
        if level==0:
          self.backpropped[tstart,tstop] = (u,y)
  
      seq_x = self.getSequenceVector(tstop,None,level)
  
      g0.addWeightTensors((seq_x,))
      for i,t in enumerate(y):
        g0.replaceTensor(t,i)
  # end eval

  def getPrimalWithGrad(self,tstart,tstop,level):
    """ 
    Get the forward solution associated with this
    time step and also get its derivative. This is
    used by the BackwardApp in computation of the
    adjoint (backprop) state and parameter derivatives.
    Its intent is to abstract the forward solution
    so it can be stored internally instead of
    being recomputed.
    """
    
    # use the short cut precomputed (with derivatives)
    if level==0 and (tstart,tstop) in self.backpropped:
      with self.timer("getPrimalWithGrad-short"):
        u,y = self.backpropped[(tstart,tstop)]
      return y,u

    with self.timer("getPrimalWithGrad-long"):
      # extract teh various vectors for this value from the fine level to linearize around
      b_u = self.getUVector(0,tstart)

      seq_x = b_u.weightTensors()[0]
      u = tuple([v.detach() for v in b_u.tensors()])

      for t in u:
        t.requires_grad = True
  
      # evaluate the step
      with torch.enable_grad():
        y = self.computeStep(level,tstart,tstop,seq_x,u)
   
    return y, u
  # end getPrimalWithGrad

# end ForwardBraidApp

##############################################################

class BackwardBraidApp(parent.BraidApp):

  def __init__(self,fwd_app,timer_manager,abs_tol):
    # call parent constructor
    parent.BraidApp.__init__(self,'RNN',fwd_app.getMPIComm(),
                          fwd_app.local_num_steps,
                          fwd_app.Tf,
                          fwd_app.max_levels,
                          fwd_app.max_iters,spatial_ref_pair=None,require_storage=True,abs_tol=abs_tol)

    self.fwd_app = fwd_app

    # build up the core
    self.py_core = self.initCore()

    # reverse ordering for adjoint/backprop
    self.setRevertedRanks(1)

    # force evaluation of gradients at end of up-cycle
    self.finalRelax()

    self.timer_manager = timer_manager
  # end __init__

  def initializeVector(self,t,x):
    # this is being really careful, can't
    # change the intial condition
    if t!=0.0:
      for ten in x.tensors():
        ten[:] = 0.0

  def __del__(self):
    self.fwd_app = None

  def getTensorShapes(self):
    return self.shape0

  def timer(self,name):
    return self.timer_manager.timer("BckWD::"+name)

  def run(self,x):

    try:
      self.RNN_models = self.fwd_app.RNN_models

      f = self.runBraid(x)

      self.grads = [p.grad.detach().clone() for p in self.RNN_models.parameters()]

      # required otherwise we will re-add the gradients
      self.RNN_models.zero_grad() 

      self.RNN_models = None
    except:
      print('\n**** Torchbraid Internal Exception ****\n')
      traceback.print_exc()

    return f
  # end forward

  def eval(self,w,tstart,tstop,level,done):
    """
    Evaluate the adjoint problem for a single time step. Here 'w' is the
    adjoint solution. The variables 'x' and 'y' refer to the forward
    problem solutions at the beginning (x) and end (y) of the type step.
    """
    with self.timer("eval"):
      try:
        # we need to adjust the time step values to reverse with the adjoint
        # this is so that the renumbering used by the backward problem is properly adjusted
        t_y,t_x = self.fwd_app.getPrimalWithGrad(self.Tf-tstop,self.Tf-tstart,level)

        # play with the parameter gradients to make sure they are on apprpriately,
        # store the initial state so we can revert them later
        required_grad_state = []
        if done!=1:
          for p in self.RNN_models.parameters(): 
            required_grad_state += [p.requires_grad]
            p.requires_grad = False

        # perform adjoint computation
        t_w = w.tensors()
        s_w = torch.stack(t_w)
        with torch.enable_grad():
          s_y = torch.stack(t_y)
        s_w.requires_grad = False
        s_y.backward(s_w,retain_graph=True)

        # this little bit of pytorch magic ensures the gradient isn't
        # stored too long in this calculation (in particulcar setting
        # the grad to None after saving it and returning it to braid)
        for wv,xv in zip(t_w,t_x):
          wv.copy_(xv.grad.detach()) 
          xv.grad = None

        # revert the gradient state to where they started
        if done!=1:
          for p,s in zip(self.RNN_models.parameters(),required_grad_state):
            p.requires_grad = s
      except:
        print('\n**** Torchbraid Internal Exception ****\n')
        traceback.print_exc()
  # end eval

# end BackwardODENetApp
