import subprocess

def check_sys_proc_exists_by_name(proc_name):
    # result = os.system('ps aux|grep ' + proc_name + '| grep -v grep | wc -l')
    result = subprocess.check_output('ps aux|grep ' + proc_name + '| grep -v grep | wc -l', shell=True)
    if int(result) > 0:
        return True
    return False


if __name__ == '__main__':
    result = check_sys_proc_exists_by_name('edu.stanford.nlp.pipeline.StanfordCoreNLPServer')
    # result = check_sys_proc_by_name('java')

    print('result:', result)