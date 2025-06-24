from skytap.skytap import SkytapClient

client = SkytapClient()
client.set_authorization()

print(client.get_departments())
print(client.get_users())
print(client.get_bitly_url("https://www.google.com"))