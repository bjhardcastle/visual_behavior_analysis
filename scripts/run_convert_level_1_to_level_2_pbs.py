import sys
import platform
if platform.system() == 'Linux':
    sys.path.append('/allen/programs/braintv/workgroups/nc-ophys/Doug/pbstools')
from pbstools import PythonJob # flake8: noqa: E999

# #VisualBehaviorDevelopment - complete dataset as of 11/15/18
# lims_ids = [639253368, 639438856, 639769395, 639932228, 644942849, 645035903,
#        645086795, 645362806, 646922970, 647108734, 647551128, 647887770,
#        648647430, 649118720, 649318212, 661423848, 663771245, 663773621,
#        664886336, 665285900, 665286182, 670396087, 671152642, 672185644,
#        672584839, 673139359, 673460976, 685744008, 686726085, 692342909,
#        692841424, 693272975, 693862238, 695471168, 696136550, 698244621,
#        698724265, 700914412, 701325132, 702134928, 702723649, 712178916,
#        712860764, 713525580, 714126693, 715161256, 715228642, 715887471,
#        715887497, 716327871, 716337289, 716600289, 716602547, 719321260,
#        719996589, 720001924, 720793118, 723037901, 723064523, 723748162,
#        723750115, 729951441, 730863840, 731936595, 732911072, 733691636,
#        736490031, 736927574, 737471012, 745353761, 745637183, 747248249,
#        750469573, 751935154, 752966796, 753931104, 754552635, 754566180,
#        754943841, 756715598, 758274779, 760003838, 760400119, 760696146,
#        760986090, 761861597, 762214438, 762214650, 766779984, 767424894,
#        768223868, 768224465, 768225217, 768865460, 768871217, 769514560,
#        770094844, 771381093, 771427955, 772131949, 772696884, 772735942,
#        773816712, 773843260, 774370025, 774379465, 775011398, 775429615,
#        776042634]

lims_ids = [664886336, 665285900, 685744008, 686726085, 771381093, 771427955, 772131949,
772696884, 772735942, 773816712, 773843260, 774370025, 774379465, 775011398, 775429615, 776042634, 756565411]

#VisBehIntTestDatacube
# lims_ids = [742828015, 742828595, 743160774, 743161105, 744540132, 744540163,
#        744540350, 746257283, 746257362, 746425946, 746425960, 746426152,
#        746445059, 746445153, 746445167, 746445294, 746447351, 747305983,
#        747321339, 747321353, 750535101, 750536682, 750536778, 750846133,
#        750850855, 750852080, 750852098, 753089326, 754045120, 754056568,
#        754064001, 754065714, 754068181, 754068195, 754090999, 754091013,
#        754108308, 754108616, 754108630, 754108824, 754588569, 754588583,
#        754845811, 755001578, 755008064, 755011059, 755014874, 755647750,
#        755647764, 755649776, 755649889, 755650903, 756119038, 756119052,
#        756119239, 756131192, 756812463, 756812477, 756812552, 756813628,
#        757628349, 757628365, 757628501, 757945399, 758312489, 758319777,
#        759036676, 759037388, 759037655, 759276375, 759283774, 759283789,
#        759283945, 759580717, 759580731, 759841294, 760095646, 760095646,
#        760097843, 760097843, 760097857, 760097947, 760097947, 760098070,
#        760098185, 760098363, 760098363, 760598315, 760603437, 760603437,
#        760603451, 760603451, 760604597, 760604597, 760604901, 760604901,
#        760604919, 760604919, 760767168, 760767168, 760767396, 760767396,
#        760767427, 760767427, 760767562, 760767562, 761058425, 761058739,
#        761059374, 761059374, 761059388, 761059388, 761059782, 761607566,
#        761607566, 761867107, 762166213]

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
