#include "channel.h"
#include "sysutil.h"
#include "timing.h"
#include <sys/wait.h>
#include <unistd.h>
#include <vector>
#include <cstring>
#include <stdexcept>
void run_echo(Channel& c,size_t size,size_t iters){c.setup(size);int ctl[2];if(pipe(ctl))throw std::runtime_error("control pipe");pid_t pid=fork();if(pid<0)throw std::runtime_error("fork");if(pid==0){close(ctl[0]);c.attach(1);std::vector<char>b(size);for(size_t i=0;i<iters;i++){c.recv(b.data(),size);c.send(b.data(),size);}c.teardown(1);_exit(0);}close(ctl[1]);c.attach(0);std::vector<char>b(size,'x'),out(size);for(size_t i=0;i<iters;i++){c.send(b.data(),size);c.recv(out.data(),size);if(out!=b)throw std::runtime_error("integrity failure");}int st;waitpid(pid,&st,0);c.teardown(0);}
