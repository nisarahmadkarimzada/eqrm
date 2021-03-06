import os
import sys

import unittest
import tempfile

from scipy import array, asarray, allclose, concatenate, newaxis, log, exp

from eqrm_code.regolith_amplification_model import *
from eqrm_code.util import dict2csv


class Test_Regolith_Amplification_Model(unittest.TestCase):
        
    def test_bin_indicies(self):
        #/(mean_log_amp*log_ground_motion)

        # test bin_indices
        pga=[0]
        moment_magnitude=[0]
        periods=[0]
        log_amplifications={}
        log_stds={}
        amp_model=Regolith_amplification_model(pga,moment_magnitude,periods,
                                               log_amplifications,log_stds)

        values=array((4.0,4.9,5.0,5.1,5.5,7,8))
        bin_points=array((4.5,5.5,7))
        assert allclose(amp_model._bin_indices(values,bin_points),
                array((0,0,0,1,1,2,2)))
        # may fail on borders if anything changes
        
    def test_amplification_model_parameters_from_xml(self):
        handle, file_name = tempfile.mkstemp('.xml', __name__+'_')
        os.close(handle)
        handle = open(file_name,'w')
        
        # 
        # Another example file at
        # Q:\python_eqrm\implementation_tests\input\newc_par_ampfactors.xml
        sample = """<amplification_model matlab_file = "newc_par_ars.xml">
<moment_magnitude_bins>
4.5 5.5
</moment_magnitude_bins>
<pga_bins>
0.05 0.1
</pga_bins>
<site_classes>
CD
</site_classes>
<periods>
0.0 0.01
</periods>
<site_class class="C">
    <moment_magnitude mag_bin="4.5">
        <pga pga_bin="0.05">
<log_amplification site_class = "C" moment_magnitude = "4.5" pga_bin = "0.05">
            4.5 0.05
            </log_amplification>
<log_std site_class = "C" moment_magnitude = "4.5" pga_bin = "0.05">
            45 5
</log_std>
        </pga>
        <pga pga_bin="0.1">
<log_amplification site_class = "C" moment_magnitude = "4.5" pga_bin = "0.1">
            4.5 0.1 
            </log_amplification>
    <log_std site_class = "C" moment_magnitude = "4.5" pga_bin = "0.1">
            45 1
            </log_std>
        </pga>
        </moment_magnitude>
    <moment_magnitude mag_bin="5.5">
        <pga pga_bin="0.05">
<log_amplification site_class = "C" moment_magnitude = "5.5" pga_bin = "0.05">
            35.5 3.05
            </log_amplification>
    <log_std site_class = "C" moment_magnitude = "5.5" pga_bin = "0.05">
            355 305 
            </log_std>
        </pga>
        <pga pga_bin="0.1">
<log_amplification site_class = "C" moment_magnitude = "5.5" pga_bin = "0.1">
            35.5 30.1
            </log_amplification>
            <log_std site_class = "C" moment_magnitude = "5.5" pga_bin = "0.1">
            355 301
            </log_std>
        </pga>
    </moment_magnitude>
</site_class>

<site_class class="D">
    <moment_magnitude mag_bin="4.5">
        <pga pga_bin="0.05">
<log_amplification site_class = "D" moment_magnitude = "4.5" pga_bin = "0.05">
            0.4 0.5
            </log_amplification>
<log_std site_class = "D" moment_magnitude = "4.5" pga_bin = "0.05">
0.3 0.4
</log_std>
        </pga>
        <pga pga_bin="0.1">
<log_amplification site_class = "D" moment_magnitude = "4.5" pga_bin = "0.1">
            0.45 0.45
            </log_amplification>
    <log_std site_class = "D" moment_magnitude = "4.5" pga_bin = "0.1">
             0.045 0.045
            </log_std>
        </pga>
        </moment_magnitude>
    <moment_magnitude mag_bin="5.5">
        <pga pga_bin="0.05">
<log_amplification site_class = "D" moment_magnitude = "5.5" pga_bin = "0.05">
            5.5 0.05
            </log_amplification>
    <log_std site_class = "D" moment_magnitude = "5.5" pga_bin = "0.05">
           5.5 0.005
            </log_std>
        </pga>
        <pga pga_bin="0.1">
<log_amplification site_class = "D" moment_magnitude = "5.5" pga_bin = "0.1">
            5.5 0.1
            </log_amplification>
            <log_std site_class = "D" moment_magnitude = "5.5" pga_bin = "0.1">
            5.5 0.01
            </log_std>
        </pga>
    </moment_magnitude>
</site_class>
</amplification_model>
        """
        handle.write(sample)
        handle.close()
        pga_bins,moment_mag_bins,periods,log_amps,log_stds = \
                 amplification_model_parameters_from_xml(file_name)
        pga_bins_act = [0.05, 0.1]
        moment_mag_bins_act = [4.5, 5.5]
        periods_act = [0.0, 0.01]
        log_amps_act = {'C': array([[[4.5, 0.05],
                                     [4.5, 0.1]],
                                    [[35.5, 3.05],
                                     [35.5, 30.1]]]),
                        'D': array([[[0.4, 0.5],
                                     [0.45, 0.45]],
                                    [[5.5, 0.05],
                                     [5.5, 0.1]]])
                        }
        log_stds_act = {'C': array([[[45, 5],
                                     [45, 1]],
                                    [[355, 305],
                                     [355, 301]]]),
                        'D': array([[[0.3, 0.4],
                                     [0.045, 0.045]],
                                    [[5.5, 0.005],
                                     [5.5, 0.01]]])
                        }
        self.failUnless(allclose(pga_bins, pga_bins_act),
                        'Failed!')
        self.failUnless(allclose(moment_mag_bins, moment_mag_bins_act),
                        'Failed!')
        self.failUnless(allclose(periods, periods_act),
                        'Failed!')
        for key in ['C', 'D']:
            self.failUnless(allclose(log_amps[key], log_amps_act[key]) ,
                            'Failed!')
            self.failUnless(allclose(log_stds[key], log_stds_act[key]) ,
                            'Failed!')
            
        model = Regolith_amplification_model.from_xml(file_name)
        self.failUnless(allclose(model.pga_bins, pga_bins_act),
                        'Failed!')
        self.failUnless(allclose(model.moment_magnitude_bins,
                                 moment_mag_bins_act),
                        'Failed!')
        self.failUnless(allclose(model.periods, periods_act),
                        'Failed!')
        for key in ['C', 'D']:
            self.failUnless(allclose(model.log_amplifications[key],
                                     log_amps_act[key]) ,
                            'Failed!')
            self.failUnless(allclose(model.log_stds[key], log_stds_act[key]) ,
                            'Failed!')

        os.remove(file_name)

    def test_load_site_class2Vs30(self):
        a = 60.0
        b = 2.0
        title_index_dic = {
            'site_class':0,
            'vs30':1}
        attribute_dic = {
            'site_class':['A','B'],
            'vs30':[a,b]}
        answer = {'A':60., 'B':2.0}
        
        handle, file_name = tempfile.mkstemp('.csv','test_regolith_')
        os.close(handle)
        dict2csv(file_name, title_index_dic, attribute_dic)
        results = load_site_class2Vs30(file_name)
        os.remove(file_name)
        #print "results",results 
        self.failUnless(results == answer,  'Failed!')
        
    def test_load_site_class2Vs30_2(self):
        a = 60.0
        b = 2.0
        title_index_dic = {
            'site_class':0,
            'vs30':1}
        attribute_dic = {
            'site_class':['A','B'],
            'vs30':[a,b]}
        answer = {'A':60., 'B':2.0}
        
        handle, file_name = tempfile.mkstemp('.csv','test_regolith_')
        os.close(handle)
        dict2csv(file_name, title_index_dic, attribute_dic)
        file_handle = open(file_name,"rb")
        results = load_site_class2Vs30(file_handle)
        os.remove(file_name)
        self.failUnless(results == answer,  'Failed!')

    def test_load_site_class2Vs30_bad(self):
        a = 60.0
        b = 2.0
        title_index_dic = {
            'site_class':0,
            'vs30yeah':1}
        attribute_dic = {
            'site_class':['A','B'],
            'vs30yeah':[a,b]}
        answer = {'A':60., 'B':2.0}
        
        handle, file_name = tempfile.mkstemp('.csv','test_regolith_')
        os.close(handle)
        dict2csv(file_name, title_index_dic, attribute_dic)
        try:
            results = load_site_class2Vs30(file_name)
        except IOError:
            os.remove(file_name)
            pass
        else:
            os.remove(file_name)
            self.failUnless(False, "KeyError not raised")
            
        
#-------------------------------------------------------------
if __name__ == "__main__":
    suite = unittest.makeSuite(Test_Regolith_Amplification_Model,'test')
    #suite = unittest.makeSuite(Test_Regolith_Amplification_Model,'test_site_class_names')
    runner = unittest.TextTestRunner()
    runner.run(suite)


