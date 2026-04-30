import socket
try:
    import dns.resolver
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']
    
    domains = ['fastdl.app', 'snapinsta.to', 'api.vyturex.com', 'co.wuk.sh']
    for d in domains:
        try:
            answers = resolver.resolve(d, 'A')
            print(f"{d}: {[rdata.address for rdata in answers]}")
        except Exception as e:
            print(f"Failed to resolve {d}: {e}")
except ImportError:
    print("dnspython not installed")
