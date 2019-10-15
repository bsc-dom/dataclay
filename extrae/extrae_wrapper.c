#include "extrae_internals.h"
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

static int __TASKID = 0;
static int __NUMTASKS = 1;

static unsigned int get_task_id(void)
{ return __TASKID; }

static unsigned int get_num_tasks(void)
{ return __NUMTASKS; }

void set_task_id(int id)
{
	printf("%s %i\n","** dataClay Extrae Wrapper successfully loaded! Task ID = ", id);

        __TASKID = id;
        Extrae_set_taskid_function (get_task_id);
}

void set_num_tasks(int num_tasks)
{
	printf("%s %i\n","** dataClay Extrae Wrapper: Num Tasks = ", num_tasks);

        __NUMTASKS = num_tasks;
        Extrae_set_numtasks_function (get_num_tasks);
}

