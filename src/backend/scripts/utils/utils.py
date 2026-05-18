def parse_url(url):
    port = url[-4:]
    slash_index = url.rfind("/")
    colon_index = url.rfind(":")
    host = url[slash_index + 1:colon_index]

    return port, host