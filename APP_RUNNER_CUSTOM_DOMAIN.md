# App Runner Custom Domain - DNS Record Types

## Quick Answer

**It depends on your domain setup:**

- **Subdomain** (e.g., `app.yourdomain.com`): Use **CNAME**
- **Root domain** (e.g., `yourdomain.com`): 
  - **Route 53**: Use **ALIAS** (recommended)
  - **Other DNS providers**: Use **A record** (if supported) or redirect to subdomain

## Detailed Explanation

### CNAME Record

**Use for**: Subdomains (www, app, portfolio, etc.)

**Example**: `app.yourdomain.com` → App Runner domain

**Pros**:
- ✅ Works with any DNS provider
- ✅ Easy to set up
- ✅ Standard DNS record type
- ✅ Automatically updates if App Runner domain changes

**Cons**:
- ❌ Cannot be used for root domain (`yourdomain.com`)
- ❌ Some DNS providers have limitations

**When to use**:
- You're using a subdomain (recommended)
- You're not using Route 53
- You want the simplest setup

### ALIAS Record (Route 53 Only)

**Use for**: Root domain or subdomain (Route 53 only)

**Example**: `yourdomain.com` → App Runner domain

**Pros**:
- ✅ Works for root domain (apex domain)
- ✅ Works like CNAME but can be used at root
- ✅ Automatically resolves to IP addresses
- ✅ Free (no additional queries)
- ✅ Automatically updates

**Cons**:
- ❌ Only available with AWS Route 53
- ❌ Not available with other DNS providers

**When to use**:
- You're using Route 53
- You want to use root domain (`yourdomain.com`)
- You want automatic IP resolution

## Recommendations by Scenario

### Scenario 1: Using Subdomain (Most Common)

**Domain**: `app.yourdomain.com` or `portfolio.yourdomain.com`

**DNS Provider**: Any (Route 53, Cloudflare, GoDaddy, etc.)

**Record Type**: **CNAME**

**Setup**:
1. In your DNS provider, create CNAME record:
   - **Name**: `app` (or `portfolio`)
   - **Type**: CNAME
   - **Value**: Your App Runner domain (e.g., `xxxxx.us-east-1.awsapprunner.com`)
   - **TTL**: 300 (or default)

2. In App Runner, add custom domain: `app.yourdomain.com`

**This is the recommended approach!** ✅

### Scenario 2: Using Root Domain with Route 53

**Domain**: `yourdomain.com`

**DNS Provider**: AWS Route 53

**Record Type**: **ALIAS**

**Setup**:
1. In Route 53, create ALIAS record:
   - **Name**: (leave blank for root, or `@`)
   - **Type**: A (ALIAS)
   - **Alias Target**: Select your App Runner service
   - **Evaluate Target Health**: Yes (recommended)

2. In App Runner, add custom domain: `yourdomain.com`

### Scenario 3: Using Root Domain with Other DNS Providers

**Domain**: `yourdomain.com`

**DNS Provider**: Cloudflare, GoDaddy, Namecheap, etc.

**Options**:

**Option A - Redirect to Subdomain** (Recommended):
- Use CNAME for `www.yourdomain.com` → App Runner
- Redirect `yourdomain.com` → `www.yourdomain.com`
- Most DNS providers support this

**Option B - A Record** (If supported):
- Some providers support A records that point to App Runner
- Check your provider's documentation
- Less flexible than ALIAS

## Step-by-Step: Adding Custom Domain

### In App Runner:

1. Go to App Runner → Your service
2. Click "Custom domains" tab
3. Click "Add domain"
4. Enter your domain: `app.yourdomain.com` (or root domain)
5. App Runner will show you:
   - **Domain name**: Your custom domain
   - **Status**: Pending validation
   - **DNS records to add**: The CNAME or ALIAS record details

### In Your DNS Provider:

**For CNAME (Subdomain)**:
```
Type: CNAME
Name: app (or www, portfolio, etc.)
Value: xxxxx.us-east-1.awsapprunner.com
TTL: 300
```

**For ALIAS (Route 53, Root Domain)**:
```
Type: A (ALIAS)
Name: (blank for root)
Alias: Yes
Alias Target: [Select App Runner service]
```

## Best Practice Recommendation

**Use a subdomain with CNAME**:
- ✅ Works everywhere
- ✅ Simplest setup
- ✅ Most flexible
- ✅ Easy to change later

**Example**:
- `app.yourdomain.com` → App Runner (CNAME)
- `yourdomain.com` → Redirects to `app.yourdomain.com`

## Verification

After adding DNS records:

1. **Wait for DNS propagation** (5-60 minutes)
2. **Check in App Runner**: Custom domains tab should show "Active"
3. **Test**: Visit your custom domain in browser
4. **Verify SSL**: App Runner automatically provisions SSL certificate

## Troubleshooting

### "Pending validation" Status

- DNS records not propagated yet (wait 5-60 minutes)
- DNS records incorrect (double-check values)
- Wrong record type (use CNAME for subdomain)

### SSL Certificate Issues

- App Runner automatically provisions SSL
- Takes 10-30 minutes after DNS is active
- Check App Runner custom domains tab for status

## Summary

| Domain Type | DNS Provider | Record Type | Recommendation |
|-------------|--------------|-------------|----------------|
| Subdomain | Any | **CNAME** | ✅ Recommended |
| Root | Route 53 | **ALIAS** | ✅ Works |
| Root | Other | Redirect to subdomain | ✅ Recommended |

**For most users**: Use a subdomain (e.g., `app.yourdomain.com`) with **CNAME** record. This is the simplest and most reliable option.

