# DataClay Application Benchmark Results

<!-- The script performs [Brief description of what the script does]. -->

*Each benchmark run was executed three times to ensure consistency and reliability of the results.*

## Benchmark 2024-05-15

- **Supercomputer Name:** MareNostrum 5
- **dataClay version:** edge (3.1.1.dev)
- **COMPSs version:** ???

### Iterations: 1000

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 0.75646               | 0.66808               | 0.23325           | 1.15998                   |
| Run 2     | 0.75913               | 0.67283               | 0.64444           | 1.17200                   |
| Run 2     | 0.76021               | 0.68074               | 44.34103           | 1.20933                   |

### Iterations: 10_000

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | ???????               | ???????               | ???????           | ???????                   |

## Benchmark 2023

- **Supercomputer Name:** MareNostrum 4
- **dataClay version:** 3.1.0
- **COMPSs version:** 3.2

*Each benchmark run was executed three times to ensure consistency and reliability of the results.*

### Iterations: 1000

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 1.32540               | 0.91725               | 0.11181           | 1.38091                   |
| **Avg**   | **1.32540**           | **0.91725**           | **0.11181**       | **1.38091**               |

### Iterations: 10_000

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 15.40256               | 7.55768               | 3.27596           | 24.88401                   |
| **Avg**   | **15.40256**           | **7.55768**           | **3.27596**       | **24.88401**               |

### Iterations: 100_000

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 164.41901               | 120.31077               | 39.86417           | 323.71481                   |
| **Avg**   | **164.41901**           | **120.31077**           | **39.86417**       | **323.71481**               |

### Iterations: 100_000 (redis_cluster)

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 549.42915               | 101.78536               | 44.86119           | 325.89406                   |
| **Avg**   | **549.42915**           | **101.78536**           | **44.86119**       | **325.89406**               |

### Iterations: 1000 - COMPSs - 2 backends (1 per socket)

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 3.89035               | 1.57359               | ???????           | ???????                   |
| **Avg**   | **3.89035**           | **1.57359**           | **???????**       | **???????**               |

### Iterations: 10_000 - COMPSs - 2 backends (1 per socket)

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 26.28644               | 14.99796               | ???????           | ???????                   |
| **Avg**   | **26.28644**           | **14.99796**           | **???????**       | **???????**               |

### Iterations: 100_000 - COMPSs - 2 backends (1 per socket)

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 183.97537               | 179.85352               | ???????           | ???????                   |
| **Avg**   | **183.97537**           | **179.85352**           | **???????**       | **???????**               |

### Iterations: 100_000 - COMPSs - 6 backends (1 per socket)

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | 86.46714               | 106.98263               | ???????           | ???????                   |
| **Avg**   | **86.46714**           | **106.98263**           | **???????**       | **???????**               |

## TEMPLATE Benchmark [DATE]

- **Supercomputer Name:** ???
- **dataClay version:** ???
- **COMPSs version:** ???

### Iterations: [NUM_ITERATIONS]

| Execution | make_persistent (sec) | read all values (sec) | flush_all (sec)   | load and read all (sec)   |
|-----------|-----------------------|-----------------------|-------------------|---------------------------|
| Run 1     | ???????               | ???????               | ???????           | ???????                   |
| Run 2     | ???????               | ???????               | ???????           | ???????                   |
| Run 3     | ???????               | ???????               | ???????           | ???????                   |
| **Avg**   | **???????**           | **???????**           | **???????**       | **???????**               |
