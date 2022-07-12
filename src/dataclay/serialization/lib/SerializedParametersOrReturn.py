class SerializedParametersOrReturn(object):
    def __init__(
        self, num_params=0, imm_objs=dict(), lang_objs=dict(), vol_objs=dict(), pers_objs=dict()
    ):
        """
        Serialized parameters or return
        :param num_params: number of parameters
        :param imm_objs: immutable objects
        :param lang_objs: language objects
        :param vol_objs: volatile objects
        :param pers_objs: persistent objects refs
        """
        self.num_params = num_params
        self.imm_objs = imm_objs
        self.lang_objs = lang_objs
        self.vol_objs = vol_objs
        self.persistent_refs = pers_objs
