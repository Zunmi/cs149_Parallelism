#include "../tasksys.cpp"
#include <dirent.h>

static void CheckTask(void *data, int, int, int taskIndex, int taskCount,
                      int, int, int, int, int, int) {
    assert(taskCount == 257);
    ((int *)data)[taskIndex]++;
}

int main() {
    cpu_set_t allowedCPUs;
    assert(sched_getaffinity(0, sizeof(allowedCPUs), &allowedCPUs) == 0);
    const int allowedCount = CPU_COUNT(&allowedCPUs);
    InitTaskSystem();

    DIR *taskDirectory = opendir("/proc/self/task");
    assert(taskDirectory != nullptr);
    int threadCount = 0;
    while (dirent *entry = readdir(taskDirectory)) {
        if (entry->d_name[0] >= '0' && entry->d_name[0] <= '9')
            threadCount++;
    }
    closedir(taskDirectory);
    if (threadCount != allowedCount) {
        fprintf(stderr, "FAIL: %d OS threads for %d allowed CPUs\n", threadCount, allowedCount);
        return 1;
    }

    int executions[257] = {};
    for (int round = 0; round < 2; round++) {
        void *handle = nullptr;
        ISPCLaunch(&handle, (void *)CheckTask, executions, 257, 1, 1);
        ISPCSync(handle);
        for (int count : executions)
            assert(count == round + 1);
    }
    printf("PASS: %d allowed CPUs, %d OS threads, 257 tasks executed exactly once per round\n",
           allowedCount, threadCount);
}
