import pandas as pd
import time
import pytest

from visual_behavior.translator.foraging2 import data_to_change_detection_core
from visual_behavior.translator.core import create_extended_dataframe
from visual_behavior.validation.qc import generate_qc_report

# some sessions that have been manually validated. These should all pass the QC functions.
sessions = {
    'TRAINING_1_gratings_412629':'//allen/programs/braintv/production/visualbehavior/prod0/specimen_756572266/behavior_session_781827134/181119092559_412629_a3775e3e-e1ca-474a-b413-91cccd6d886f.pkl',
    'TRAINING_1_gratings_421137': '//allen/programs/braintv/production/visualbehavior/prod0/specimen_760928877/behavior_session_781938249/181119102010_421137_c108dc71-ef5e-46ad-8d85-8da0fdaf7d3d.pkl',
    'TRAINING_1_gratings_412619': '//allen/programs/braintv/production/visualbehavior/prod0/specimen_756572266/behavior_session_781827134/181119092559_412629_a3775e3e-e1ca-474a-b413-91cccd6d886f.pkl',
    'TRAINING_2_gratings_flashed_416656': '//allen/programs/braintv/production/visualbehavior/prod0/specimen_760937126/behavior_session_782345413/181119150503_416656_2b0893fe-843d-495e-bceb-83b13f2b02dc.pkl',
    'TRAINING_3_images_A_10uL_reward_424460': '//allen/programs/braintv/production/visualbehavior/prod0/specimen_759499601/behavior_session_782276944/181119135416_424460_b6daf247-2caf-4f38-9eb1-ab97825923cd.pkl',
    'TRAINING_4_images_A_handoff_ready_402329': '//allen/programs/braintv/production/visualbehavior/prod0/specimen_722884870/behavior_session_782264775/181119134201_402329_b75a87d0-8178-4171-a3b2-7cea3ae8e118.pkl',
    'OPHYS_IMAGES_A_412364': '//allen/programs/braintv/production/visualbehavior/prod0/specimen_744935649/ophys_session_778113069/778113069_stim.pkl',
}

# look up pytest skipif, skipif(~os.path.exists(//allen))


class DataCheck(object):
    # a simple class for loading data, running qc
    def __init__(self, pkl_path):
        self.pkl_path = pkl_path
        self.load_data()
        self.run_qc()

    def load_data(self):

        self.data = pd.read_pickle(self.pkl_path)
        self.core_data = data_to_change_detection_core(self.data)

    def run_qc(self):
        self.qc = generate_qc_report(self.core_data)


@pytest.mark.parametrize("session_key, filename", sessions.items())
def test_sessions(session_key, filename):
    data_result = DataCheck(filename)
    assert(data_result.qc['passes'] == True)


if __name__ == '__main__':
    test_sessions(*list(sessions.items())[-1])
    print('all sessions passed')
