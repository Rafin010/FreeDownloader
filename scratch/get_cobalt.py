import urllib.request
import json
import dns.resolver

def get_cobalt_instances():
    try:
        # Resolve manually via 8.8.8.8
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8']
        answers = resolver.resolve('instances.cobalt.tools', 'A')
        ip = answers[0].address
        
        req = urllib.request.Request("https://instances.cobalt.tools/instances.json", headers={
            'User-Agent': 'Mozilla/5.0'
        })
        # Override host in urllib? Easier to just replace the host with IP and add Host header
        req = urllib.request.Request(f"https://{ip}/instances.json", headers={
            'User-Agent': 'Mozilla/5.0',
            'Host': 'instances.cobalt.tools'
        })
        
        # We need to disable SSL verification because the IP won't match the certificate SNI probably
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Got {len(data)} instances.")
            
            working_urls = []
            for instance in data:
                # Find instances that are online and have score > 0
                if instance.get('api_online') and instance.get('score', 0) > 0:
                    domain = instance.get('domain')
                    if domain:
                        working_urls.append(f"https://{domain}")
            
            print("Working Domains:", working_urls[:20])
            with open('working_cobalt.json', 'w') as f:
                json.dump(working_urls, f)
            
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    get_cobalt_instances()
