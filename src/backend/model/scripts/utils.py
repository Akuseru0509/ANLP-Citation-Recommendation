import os
import torch
import glob

def save_model(module_dicts ,save_name , max_to_keep = 0, overwrite = True):
    folder_path = os.path.dirname(os.path.abspath(save_name))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    state_dicts = {}
    for key in module_dicts.keys():
        if isinstance(module_dicts[key], torch.nn.DataParallel):
            state_dicts[key] = module_dicts[key].module.state_dict()
        elif isinstance(module_dicts[key], torch.nn.Module):
            state_dicts[key] = module_dicts[key].state_dict()
        else:
            state_dicts[key] = module_dicts[key]

    if os.path.exists(save_name):
        if overwrite:
            os.remove(save_name)
            torch.save(state_dicts, save_name)
        else:
            print("Warning: checkpoint file already exists!")
            return
    else:
        torch.save(state_dicts, save_name)

    if max_to_keep > 0:
        pt_file_list = glob(folder_path+"/*.pt")
        pt_file_list.sort(key= lambda x: os.path.getmtime(x))
        for idx in range(len(pt_file_list) - max_to_keep):
            os.remove(pt_file_list[idx])

