# Results

## latest

### MN4 - only dataclay - sequential

**1000 iterations**:

- Time make_persistent: 1.32540 seconds
- Time read all values: 0.91725 seconds
- Time flush_all: 0.11181 seconds
- Time load and read all values: 1.38091 seconds

**10000 iterations**:

- Time make_persistent: 15.40256 seconds
- Time read all values: 7.55768 seconds
- Time flush_all: 3.27596 seconds
- Time load and read all values: 24.88401 seconds

**100000 iterations**:

- Time make_persistent: 164.41901 seconds
- Time read all values: 120.31077 seconds
- Time flush_all: 39.86417 seconds
- Time load and read all values: 323.71481 seconds

**100000 iterations (REDIS CLUSTER)**:

- Time make_persistent: 549.42915 seconds
- Time read all values: 101.78536 seconds
- Time flush_all: 44.86119 seconds
- Time load and read all values: 325.89406 seconds

### MN4 - COMPSs

#### 2 node (2 backends) one per socket except the metadata node

**1000 iterations**:

- Time make_persistent: 3.89035 seconds
- Time read all values: 1.57359 seconds

**10000 iterations**:

- Time make_persistent: 26.28644 seconds
- Time read all values: 14.99796 seconds

**100000 iterations**:

- Time make_persistent: 183.97537 seconds
- Time read all values: 179.85352 seconds

#### 4 node (6 backends)

**100000 iterations**:

- Time make_persistent: 86.46714 seconds
- Time read all values: 106.98263 seconds
