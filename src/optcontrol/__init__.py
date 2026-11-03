"""optcontrol: optimal control from zero, for QMB 6875.

Modules
-------
tree    deterministic optimal stopping: when to cut a tree (Fisher, Faustmann)
heifer  deterministic optimal control: feeding plan + sale date (Pontryagin)
offer   stochastic control: which offer to accept (Bellman, closed form)
gold    stochastic control: the gold trader's control-limit policy (Bellman, numeric)
"""

__all__ = ["tree", "heifer", "offer", "gold"]
