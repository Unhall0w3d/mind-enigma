import subprocess


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        output = process.stdout.readline().decode().strip()
        error = process.stderr.readline().decode().strip()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output)
        if error:
            print(error)
    return process.returncode


command = "curl -s 'https://liquorix.net/install-liquorix.sh' | sudo bash"
return_code = run_command(command)
print(f"Command exited with return code: {return_code}")
