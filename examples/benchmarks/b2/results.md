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

- Time make_persistent: 157.54590 seconds
- Time read all values: 90.13104 seconds
- Time flush_all: 34.98280 seconds
- Time load and read all values: 283.70292 seconds

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
