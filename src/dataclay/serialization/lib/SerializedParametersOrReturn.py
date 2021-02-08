class SerializedParametersOrReturn(object):


    def __init__(self, num_params, imm_objs, lang_objs, vol_objs, persistent_refs):
        """
        Serialized parameters or return
        :param num_params: number of parameters
        :param imm_objs: immutable objects
        :param lang_objs: language objects
        :param vol_objs: volatile objects
        :param persistent_refs: persistent objects refs
        """
        self.num_params = num_params
        self.imm_objs = imm_objs
        self.lang_objs = lang_objs
        self.vol_objs = vol_objs
        self.persistent_refs = persistent_refs

    def __init__(self, vol_objs):
        self.num_params = dict()
        self.imm_objs = dict()
        self.lang_objs = dict()
        self.vol_objs = vol_objs
        self.persistent_refs = dict()
