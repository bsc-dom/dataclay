# from threading import Thread

# from dataclay.runtime import ReadWriteLock


# def assert_func(func, args, result):
#     assert func(*args) == result


# def test_same_thread():
#     """Many read and write locks can be acquired by the same thread."""
#     rwlock = ReadWriteLock()
#     rwlock.acquire_write()
#     rwlock.acquire_read()
#     rwlock.acquire_write()
#     rwlock.acquire_read()


# def test_read_write():
#     """A thread cannot acquire a write lock if another thread has acquired a read lock."""
#     rwlock = ReadWriteLock()

#     t = Thread(target=assert_func, args=[rwlock.acquire_read, (0,), True])
#     t.start()
#     t.join()

#     assert not rwlock.acquire_write(0)


# def test_write_read():
#     """A thread cannot acquire a read lock if another thread has acquired a write lock."""
#     rwlock = ReadWriteLock()

#     t = Thread(target=assert_func, args=[rwlock.acquire_write, (0,), True])
#     t.start()
#     t.join()

#     assert not rwlock.acquire_read(0)


# def test_write_write():
#     """A thread cannot acquire a write lock if another thread has acquired a write lock."""
#     rwlock = ReadWriteLock()

#     t = Thread(target=assert_func, args=[rwlock.acquire_write, (0,), True])
#     t.start()
#     t.join()

#     assert not rwlock.acquire_write(0)


# def test_read_read_read():
#     """Multiple threads can acquire multiple read locks."""
#     rwlock = ReadWriteLock()

#     assert rwlock.acquire_read(0)

#     t = Thread(target=assert_func, args=[rwlock.acquire_read, (0,), True])
#     t.start()
#     t.join()

#     assert rwlock.acquire_read(0)


# def test_read_write_write():
#     """A thread cannot acquire a write lock if another thread has acquired a read lock.
#     But same thread yes."""
#     rwlock = ReadWriteLock()

#     assert rwlock.acquire_read(0)

#     t = Thread(target=assert_func, args=[rwlock.acquire_write, (0,), False])
#     t.start()
#     t.join()

#     assert rwlock.acquire_write(0)


# def test_read_read_write():
#     """A thread cannot acquire a write lock if another thread has acquired a read lock."""
#     rwlock = ReadWriteLock()

#     assert rwlock.acquire_read(0)

#     t = Thread(target=assert_func, args=[rwlock.acquire_read, (0,), True])
#     t.start()
#     t.join()

#     assert not rwlock.acquire_write(0)


# # test_same_thread()
# # test_read_write()
# # test_write_read()
# # test_write_write()
# # test_read_read_read()
# # test_read_write_write()
# # test_read_read_write()
