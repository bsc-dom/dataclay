import asyncio

from dataclay.metadata.api import MetadataAPI

md = MetadataAPI("127.0.0.1", "6379")

a = asyncio.run(md.new_account("alice", "s3cret"))
md.new_account("bob", "s3cret")
md.new_account("charlie", "s3cret")

md.add_account_to_dataset("testuser", "s3cret", "testdata", "alice")
md.add_account_to_dataset("testuser", "s3cret", "testdata", "bob")
md.add_account_to_dataset("testuser", "s3cret", "testdata", "charlie")
