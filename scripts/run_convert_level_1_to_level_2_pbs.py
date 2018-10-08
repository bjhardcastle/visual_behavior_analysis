import sys
import platform
if platform.system() == 'Linux':
    sys.path.append('/allen/programs/braintv/workgroups/nc-ophys/Doug/pbstools')
from pbstools import PythonJob # flake8: noqa: E999

# #VisualBehaviorDevelopment
# lims_ids = [644942849, 645035903, 645086795, 645362806, 646922970, 647108734,
#             647551128, 647887770, 648647430, 649118720, 649318212, 639253368,
#             639438856, 639769395, 639932228, 661423848, 663771245, 663773621,
#             665286182, 673139359, 673460976, 670396087, 671152642, 672185644,
#             672584839, 695471168, 696136550, 698244621, 698724265, 700914412,
#             701325132, 702134928, 702723649, 692342909, 692841424, 693272975,
#             693862238, 712178916, 712860764, 713525580, 714126693, 715161256,
#             715887497, 716327871, 716600289, 715228642, 715887471, 716337289,
#             716602547, 720001924, 720793118, 723064523, 723750115, 719321260,
#             719996589, 723748162, 723037901, 729951441, 730863840, 736490031,
#             737471012, 731936595, 732911072, 733691636, 736927574, 745353761,
#             745637183, 747248249, 750469573, 751935154, 752966796, 753931104,
#             754552635]

#VisBehIntTestDatacube
lims_is = [760098185, 760098363, 760604901, 760767427, 760098070, 760097947,
           760604597, 760767396, 754108308, 754108824, 755014874, 754588583,
           755008064, 750846133, 754108630, 754108616, 754588569, 755011059,
           756131192, 742828595, 744540163, 746257362, 746445167, 746445153,
           750536778, 750852098, 756812552, 754056568, 754045120, 754845811,
           755001578, 755650903, 756119052, 757628349, 757628365, 759037655,
           759283789, 757945399, 758312489, 759037388, 759283774, 759580717,
           743161105, 744540132, 746425960, 746445294, 746257283, 746447351,
           747305983, 747321339, 750535101, 750852080, 754090999, 754068195,
           754064001, 759036676, 755649889, 755647750, 756119239, 756812477,
           757628501, 742828015, 743160774, 744540350, 746425946, 746426152,
           746445059, 753089326, 747321353, 750536682, 750850855, 754091013,
           754065714, 754068181, 756813628, 755647764, 755649776, 756119038,
           756812463, 758319777, 759276375, 760598315, 760097857, 760097843,
           760604919, 760767562, 759283945, 759580731, 760603437, 759841294,
           760095646, 760603451, 760767168]

python_file = r"/home/marinag/visual_behavior_analysis/scripts/convert_level_1_to_level_2.py"

jobdir = '/allen/programs/braintv/workgroups/nc-ophys/Marina/ClusterJobs/JobRecords2'

job_settings = {'queue': 'braintv',
                'mem': '60g',
                'walltime': '32:00:00',
                'ppn': 1,
                'jobdir': jobdir,
                }

for lims_id in lims_ids:
    print(lims_id)
    PythonJob(
        python_file,
        python_executable='/home/marinag/anaconda2/envs/visual_behavior_ophys/bin/python',
        python_args=lims_id,
        conda_env=None,
        jobname='process_{}'.format(lims_id),
        **job_settings
    ).run(dryrun=False)
