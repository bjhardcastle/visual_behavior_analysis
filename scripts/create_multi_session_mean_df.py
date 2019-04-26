#!/usr/bin/env python
import matplotlib
matplotlib.use('Agg')

import pandas as pd
from visual_behavior.ophys.io.create_multi_session_mean_df import get_multi_session_mean_df

if __name__ == '__main__':

    cache_dir = r'/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/visual_behavior_production_analysis'
    # manifest = pd.read_csv(os.path.join(cache_dir, 'visual_behavior_data_manifest.csv'))
    # experiment_ids = manifest.experiment_id.values

    #VisualBehavior production as of 3/20/19
    experiment_ids = [816242065, 816242073, 816242080, 816242091,
       816242095, 816242105, 816242114, 816242121, 816571905, 816571911,
       816571916, 816571919, 816571926, 816571929, 816571932, 816571934,
       825516687, 825516689, 825516691, 825516694, 825516696, 825516700,
       825516702, 825516706, 826334607, 826334610, 826334612, 826334616,
       826334620, 826334623, 826334625, 826334627, 826794703, 826794707,
       826794711, 826794714, 826794717, 826794723, 826794726, 826794730,
       828144740, 828144742, 828144744, 828144746, 828144749, 828144751,
       828144753, 828144755, 829269094, 829269096, 829269098, 829269100,
       829269102, 829269104, 829269106, 829269108, 835653625, 835653627,
       835653629, 835653631, 835653633, 835653635, 835653640, 835653642,
       838486647, 838486649, 838486651, 838486653, 838486655, 838486657,
       838486659, 838486661, 839716139, 839716141, 839716143, 839716145,
       839716147, 839716149, 839716151, 839716153, 839716706, 839716708,
       839716710, 839716712, 839716714, 839716716, 839716718, 839716720,
       840460366, 840460368, 840460370, 840460372, 840460376, 840460378,
       840460380, 840460383, 840717527, 840717529, 840717531, 840717534,
       840717536, 840717538, 840717540, 840717542, 841624549, 841624552,
       841624554, 841624556, 841624560, 841624564, 841624569, 841624576,
       841968436, 841968438, 841968440, 841968442, 841968445, 841968447,
       841968449, 841968452, 841969456, 841969458, 841969460, 841969462,
       841969465, 841969467, 841969469, 841969471, 842545433, 842545435,
       842545437, 842545439, 842545442, 842545444, 842545446, 842545448,
       842545454, 842545456, 842545458, 842545462, 842545466, 842545468,
       842545470, 842545472, 843007050, 843007052, 843007054, 843007056,
       843007058, 843007061, 843007063, 843007065, 843534729, 843534731,
       843534733, 843534736, 843534740, 843534742, 843534744, 843534746,
       844420212, 844420214, 844420217, 844420220, 844420222, 844420224,
       844420226, 844420229, 845070856, 845070858, 845070860, 845070862,
       845070864, 845070866, 845070868, 845070870, 845777907, 845777909,
       845777911, 845777913, 845777915, 845777918, 845777920, 845777922,
       845783018, 845783021, 845783023, 845783025, 845783027, 845783030,
       845783032, 845783034, 846546326, 846546328, 846546331, 846546333,
       846546335, 846546337, 846546339, 846546341, 847267616, 847267618,
       847267620, 847267622, 847267624, 847267626, 847267628, 847267630,
       848039110, 848039113, 848039115, 848039117, 848039119, 848039121,
       848039123, 848039125, 848760957, 848760959, 848760961, 848760963,
       848760965, 848760967, 848760969, 848760971, 848760974, 848760977,
       848760979, 848760981, 848760983, 848760985, 848760988, 848760990,
       849233390, 849233392, 849233394, 849233396, 849233398, 849233400,
       849233402, 849233404, 850517344, 850517346, 850517348, 850517350,
       850517352, 850517354, 850517356, 850517358, 851085092, 851085095,
       851085098, 851085100, 851085103, 851085105, 851085107, 851085109,
       851093283, 851093285, 851093287, 851093289, 851093291, 851093296,
       851093302, 851093306, 851958793, 851958795, 851958797, 851958800,
       851958802, 851958805, 851958807, 851958809, 851959317, 851959320,
       851959322, 851959324, 851959326, 851959329, 851959331, 851959333,
       852730503, 852730505, 852730508, 852730510, 852730514, 852730516,
       852730518, 852730520, 853362765, 853362767, 853362769, 853362771,
       853362773, 853362775, 853362777, 853362780, 853363739, 853363743,
       853363745, 853363747, 853363749, 853363751, 853363753, 853363756,
       853988430, 853988435, 853988437, 853988444, 853988446, 853988448,
       853988450, 853988454, 854759890, 854759894, 854759896, 854759898,
       854759900, 854759903, 854759905, 854759907, 856123117, 856123119,
       856123122, 856123124, 856123126, 856123130, 856123132, 856123134,
       856967230, 856967232, 856967234, 856967237, 856967241, 856967243,
       856967245, 856967247]

    get_multi_session_mean_df(experiment_ids, cache_dir,
                              conditions=['cell_specimen_id', 'image_name', ], flashes=True, omitted=True)
    get_multi_session_mean_df(experiment_ids, cache_dir,
                              conditions=['cell_specimen_id', 'change_image_name', 'trial_type'])
    get_multi_session_mean_df(experiment_ids, cache_dir,
                                    conditions=['cell_specimen_id', 'image_name', ], flashes=True)
    get_multi_session_mean_df(experiment_ids, cache_dir,
                                      conditions=['cell_specimen_id', 'image_name', 'repeat'], flashes=True)
    # get_multi_session_mean_df(experiment_ids, cache_dir,
    #                           conditions=['cell_specimen_id', 'change_image_name', 'behavioral_response_type'])


    # get_multi_session_mean_df(experiment_ids, cache_dir,
    #                               conditions=['cell_specimen_id', 'change_image_name', 'trial_type'], use_events=True)
    # get_multi_session_mean_df(experiment_ids, cache_dir,
    #                                       conditions=['cell_specimen_id', 'image_name', 'repeat'], flashes=True, use_events=True)
    # get_multi_session_mean_df(experiment_ids, cache_dir,
    #                                       conditions=['cell_specimen_id', 'image_name', 'engaged', 'repeat'], flashes=True, use_events=True)
    # get_multi_session_mean_df(experiment_ids, cache_dir,
    #                               conditions=['cell_specimen_id', 'change_image_name', 'behavioral_response_type'], use_events=True)
