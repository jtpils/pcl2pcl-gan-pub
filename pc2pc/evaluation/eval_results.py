import os,sys
import numpy as np
import evaluation_utils
from tqdm import tqdm
import multiprocessing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(os.path.join(ROOT_DIR, '../utils'))
import pc_util

thre = 0.03
cat_name = 'car'
#test_name = 'vanilla_ae_test'
#test_name = 'N2N_ae_test'
test_name = 'pcl2pcl_test'
#keyword2filter = '0-partial'
#keyword2filter = '-perc'
#keyword2filter = 'redo'
#keyword2filter = '_gt-retrieved'
keyword2filter = '_results_log_dimscale-align_iso-0.5'

#test_dir = '/workspace/pointnet2/pc2pc/run_%s/%s'%(cat_name, test_name)
#test_dir = '/workspace/pointnet2/pc2pc/run_3D-EPN/run_%s/%s'%(cat_name, test_name)
test_dir = '/workspace/pointnet2/pc2pc/data/3D-EPN_dataset/EPN_results/converted_txt_dim128/output-test-images-dim128'

def gt_isvalid(gt_points):
    pts_max = np.max(gt_points)
    if pts_max < 0.01:
        return False
    return True

def eval_result_folder(result_dir):
    gt_point_cloud_dir = os.path.join(result_dir, 'pcloud', 'gt')
    result_point_cloud_dir = os.path.join(result_dir, 'pcloud', 'reconstruction')

    gt_pc_names = os.listdir(gt_point_cloud_dir)
    gt_pc_names.sort()

    all_avg_dist = []
    all_comp = []
    for gt_pc_n  in (gt_pc_names):

        gt_pc_filename = os.path.join(gt_point_cloud_dir, gt_pc_n)
        re_pc_filename = os.path.join(result_point_cloud_dir, gt_pc_n)

        gt_pc_pts = pc_util.read_ply_xyz(gt_pc_filename)
        if not gt_isvalid(gt_pc_pts):
            print('Invalid gt point cloud, skip.')
            continue
        re_pc_pts = pc_util.read_ply_xyz(re_pc_filename)
        if re_pc_pts.shape[0] < 2048:
            re_pc_pts = pc_util.sample_point_cloud(re_pc_pts, 2048)

        avg_d = evaluation_utils.avg_dist(re_pc_pts, gt_pc_pts)
        comp = evaluation_utils.completeness(re_pc_pts, gt_pc_pts, thre=thre)


        all_avg_dist.append(avg_d)
        all_comp.append(comp)


    avg_dist = np.mean(all_avg_dist)
    avg_comp = np.mean(all_comp)

    print('%s - distance, completeness: %s,%s'%(result_dir, str(avg_dist), str(avg_comp)))

result_folders = os.listdir(test_dir)
result_folders.sort()

if keyword2filter is not None:
    result_folders_tmp = []
    for rs in result_folders:
        if keyword2filter in rs:
            result_folders_tmp.append(rs)
    result_folders = result_folders_tmp

num_workers = len(result_folders)

pros = []
for worker_id in range(num_workers):
    res_folder = os.path.join(test_dir, result_folders[worker_id])
    pros.append(multiprocessing.Process(target=eval_result_folder, args=(res_folder,)))
    pros[worker_id].start()
    print('start to work on:', res_folder)

for worker_id in range(num_workers):
    pros[worker_id].join()

print('Done!')