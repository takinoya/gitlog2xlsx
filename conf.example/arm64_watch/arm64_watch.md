# What is this example?
Check difference between kernel-4.8 and 4.9 .

# How to regenerate "arm64_watch.xlsx"
## Get script and target linux git repository
```bash
$ mkdir ~/gitlog2xlsx.work
$ cd ~/gitlog2xlsx.work
$ git clone https://github.com/takinoya/gitlog2xlsx.git
$ git clone --bare git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
```

## Run the script
```bash
$ cd ~/gitlog2xlsx.work/conf.example/arm64_watch/
$ python3 ../../gitlog2xlsx.py --xlsx=arm64_watch.xlsx --git=${HOME}/gitlog2xlsx.work/linux.git --range="v4.8..v4.9"
```
