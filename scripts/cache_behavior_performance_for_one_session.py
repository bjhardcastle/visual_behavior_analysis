import visual_behavior.utilities as vbu
import argparse


if __name__ == "__main__":
    # define args
    parser = argparse.ArgumentParser()
    parser.add_argument('--behavior-session-id', type=int)
    parser.add_argument('--method', type=str)

    args = parser.parse_args()
    behavior_session_id = args.behavior_session_id
    method = args.method
    print(behavior_session_id, method)
    vbu.cache_behavior_stats(behavior_session_id=behavior_session_id, method=method, per_image=False)
    vbu.cache_behavior_stats(behavior_session_id=behavior_session_id, method=method, per_image=True)
