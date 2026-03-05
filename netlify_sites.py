#!/usr/bin/env python3
"""
Netlify Sites GitHub-Style HTML Grid Generator
Creates a beautiful GitHub-style HTML grid view of all Netlify sites with live screenshots
"""

import os
import sys
import json
import requests
import webbrowser
from datetime import datetime
from pathlib import Path
from netlify import NetlifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_USERNAME = "igiteam"
DEFAULT_AVATAR = "https://github.com/igiteam.png"
DEFAULT_GITHUB_URL = "https://igiteam.github.io/"
OUTPUT_FILE = 'index.html'
OUTPUT_DIRECTORY = 'public'

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_color(text, color):
    """Print colored text"""
    print(f"{color}{text}{Colors.END}")

def safe_get(obj, attr, default=None):
    """Safely get attribute from object or key from dict"""
    if obj is None:
        return default
    
    if isinstance(obj, dict):
        return obj.get(attr, default)
    
    try:
        return getattr(obj, attr, default)
    except:
        return default

def init_client(token):
    """Initialize the Netlify client with given token"""
    try:
        client = NetlifyClient(access_token=token)
        return client
    except Exception as e:
        print_color(f"❌ Error initializing client: {e}", Colors.RED)
        return None

def format_relative_time(date_string):
    """Format date to relative time (like GitHub)"""
    if not date_string:
        return "N/A"
    try:
        # Handle string dates
        if isinstance(date_string, str):
            # Replace Z with +00:00 for proper parsing
            date_string = date_string.replace('Z', '+00:00')
            date = datetime.fromisoformat(date_string)
        else:
            date = date_string
            
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "just now"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except Exception as e:
        # If date parsing fails, return the original string
        return str(date_string)

def get_site_url(site):
    """Get the best URL for the site and ensure it uses HTTPS"""
    # Try custom domain first
    custom_domain = safe_get(site, 'custom_domain')
    if custom_domain and custom_domain.strip():
        # Ensure it's HTTPS
        if not custom_domain.startswith(('http://', 'https://')):
            return f"https://{custom_domain}"
        else:
            # If it has http://, convert to https://
            return custom_domain.replace('http://', 'https://', 1)
    
    # Try URL
    url = safe_get(site, 'url')
    if url:
        # Ensure it's HTTPS
        if url.startswith('http://'):
            return url.replace('http://', 'https://', 1)
        return url
    
    # Try ssl_url
    ssl_url = safe_get(site, 'ssl_url')
    if ssl_url:
        # Ensure it's HTTPS
        if ssl_url.startswith('http://'):
            return ssl_url.replace('http://', 'https://', 1)
        return ssl_url
    
    # Try deploy_url
    deploy_url = safe_get(site, 'deploy_url')
    if deploy_url:
        # Ensure it's HTTPS
        if deploy_url.startswith('http://'):
            return deploy_url.replace('http://', 'https://', 1)
        return deploy_url
    
    return None

def fetch_all_sites(client):
    """Fetch all sites from Netlify"""
    print_color("\n📋 Fetching your Netlify sites...", Colors.BLUE)
    
    try:
        sites = []
        if hasattr(client, 'list_sites'):
            sites = client.list_sites()
        elif hasattr(client, 'get_sites'):
            sites = client.get_sites()
        elif hasattr(client, 'sites') and hasattr(client.sites, 'list'):
            sites = client.sites.list()
        
        if not sites:
            print_color("No sites found in your account.", Colors.YELLOW)
            return []
        
        print_color(f"✨ Found {len(sites)} site(s)", Colors.GREEN)
        return sites
            
    except Exception as e:
        print_color(f"❌ Error fetching sites: {e}", Colors.RED)
        return []

def show_settings_menu():
    """Show interactive settings menu at start"""
    print("\n" + "="*60)
    print_color("🚀 NETLIFY SITES HTML GRID GENERATOR", Colors.HEADER + Colors.BOLD)
    print("="*60)
    print("\n📝 Please configure your settings:")
    print()
    
    # Get Netlify token
    token = os.getenv('NETLIFY_TOKEN', '')
    if not token or token == "your_netlify_personal_access_token_here":
        print_color("⚠️  Netlify token not found in .env file", Colors.YELLOW)
        print("You can generate one at: https://app.netlify.com/user/applications#personal-access-tokens")
        token = input("\nEnter your Netlify Personal Access Token: ").strip()
        if not token:
            print_color("❌ Token is required!", Colors.RED)
            sys.exit(1)
    
    # Get username/display name
    print(f"\n👤 Display name (default: {DEFAULT_USERNAME}):")
    username = input("Enter name: ").strip()
    if not username:
        username = DEFAULT_USERNAME
    
    # Get avatar URL
    print(f"\n🖼️  Avatar image URL (default: {DEFAULT_AVATAR}):")
    print("   Examples:")
    print("   • GitHub avatar: https://github.com/username.png")
    print("   • Custom image:  https://example.com/avatar.jpg")
    avatar = input("Enter URL: ").strip()
    if not avatar:
        avatar = DEFAULT_AVATAR
    
    # Get GitHub/website URL
    print(f"\n🔗 Profile URL (default: {DEFAULT_GITHUB_URL}):")
    print("   This is where the avatar links to")
    profile_url = input("Enter URL: ").strip()
    if not profile_url:
        profile_url = DEFAULT_GITHUB_URL
    
    print("\n" + "="*60)
    print_color("✅ Settings saved!", Colors.GREEN)
    print(f"   Username: {username}")
    print(f"   Avatar: {avatar}")
    print(f"   Profile: {profile_url}")
    print("="*60)
    
    return {
        'token': token,
        'username': username,
        'avatar': avatar,
        'profile_url': profile_url
    }

def generate_html_grid(sites, settings):
    """Generate GitHub-style HTML grid view of sites"""
    
    # Prepare site data for JavaScript
    sites_data = []
    site_cards_html = ""
    
    for site in sites:
        # Convert site to dict if it's an object
        if hasattr(site, '__dict__'):
            site_dict = site.__dict__
        else:
            site_dict = site
        
        # Get dates and ensure they're strings
        created_at = safe_get(site_dict, 'created_at', '')
        updated_at = safe_get(site_dict, 'updated_at', '')
        
        # Handle datetime objects
        if hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()
        if hasattr(updated_at, 'isoformat'):
            updated_at = updated_at.isoformat()
        
        # Get build settings
        build_settings = safe_get(site_dict, 'build_settings', {})
        if hasattr(build_settings, '__dict__'):
            build_settings = build_settings.__dict__
        
        repo_url = None
        repo_branch = 'main'
        
        if build_settings:
            if isinstance(build_settings, dict):
                repo_url = build_settings.get('repo_url')
                repo_branch = build_settings.get('repo_branch', 'main')
        
        site_info = {
            'name': safe_get(site_dict, 'name', 'Unknown'),
            'url': get_site_url(site_dict),
            'custom_domain': safe_get(site_dict, 'custom_domain', ''),
            'ssl': safe_get(site_dict, 'ssl', False),
            'plan': safe_get(site_dict, 'plan', 'free'),
            'created_at': created_at,
            'updated_at': updated_at,
            'account_name': safe_get(site_dict, 'account_name', settings['username']),
            'account_slug': safe_get(site_dict, 'account_slug', ''),
            'repo_url': repo_url,
            'repo_branch': repo_branch
        }
        sites_data.append(site_info)
        
        # Generate card HTML
        site_name = site_info['name']
        site_url = site_info['url']
        custom_domain = site_info['custom_domain'] or 'No custom domain'
        account_display = site_info['account_name'] or site_info['account_slug'] or settings['username']
        ssl_enabled = site_info['ssl']
        updated_at_relative = format_relative_time(updated_at or created_at)
        visibility = "public" if site_info['plan'] == 'free' else "private"
        
        # Screenshot URL
        screenshot_url = None
        if site_url:
            domain = site_url.replace('https://', '').replace('http://', '').split('/')[0]
            screenshot_url = f"https://img.sdappnet.cloud/?url={domain}&w=1920&h=1080"
        site_cards_html += f'''
            <div class="repo-item">
                <div class="screenshot-container" onclick="window.open('{site_url or '#'}', '_blank')">
                    <img class="screenshot" src="{screenshot_url}" loading="lazy" alt="Screenshot of {site_name}">
                    <div class="screenshot-overlay">
                        <i class="fas fa-external-link-alt"></i> Open site
                    </div>
                </div>
                <div class="repo-content">
                    <div class="repo-title">
                        <a href="{site_url or '#'}" target="_blank">{site_name}</a>
                        <span class="repo-visibility">{visibility}</span>
                    </div>
                    
                    <div class="site-details" style="margin: 12px 0; color: var(--github-text-secondary); font-size: 13px;">
                        <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-globe" style="width: 16px; color: var(--github-primary);"></i>
                            <span>{custom_domain}</span>
                        </div>
                        <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-link" style="width: 16px; color: var(--github-green);"></i>
                            <span>{site_url or 'No URL'}</span>
                        </div>
                        <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-users" style="width: 16px; color: var(--github-text-secondary);"></i>
                            <span>{account_display}</span>
                        </div>
                        {f'<div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;"><i class="fas fa-code-branch" style="width: 16px; color: #f1e05a;"></i><span>{repo_url} ({repo_branch})</span></div>' if repo_url else ''}
                    </div>
                    
                    <div class="repo-meta">
                        <div class="deploy-status">
                            <i class="fas fa-check-circle" style="color: {'var(--github-green)' if ssl_enabled else '#ef4444'};"></i>
                            <span>SSL {'Enabled' if ssl_enabled else 'Disabled'}</span>
                        </div>
                        <div class="repo-updated">
                            <span>Updated {updated_at_relative}</span>
                        </div>
                    </div>
                </div>
            </div>
        '''
    # Get the first site's screenshot for meta image (if available)
    meta_image = settings['avatar']  # default to avatar
    if sites_data and len(sites_data) > 0:
        first_site = sites_data[0]
        if first_site.get('url'):
            domain = first_site['url'].replace('https://', '').replace('http://', '').split('/')[0]
            meta_image = f"https://img.sdappnet.cloud/?url={domain}&w=1920&h=1080"
    

    # Read the HTML template with ALL curly braces escaped (doubled)
    html_template = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{username}'s Netlify Sites</title>

    <link rel="icon" href="{avatar}" type="image/x-icon">
    <link rel="apple-touch-icon" href="{avatar}" sizes="180x180">
    <link rel="icon" type="image/png" href="{avatar}" sizes="32x32">
    <link rel="icon" type="image/png" href="{avatar}"" sizes="16x16">
    <meta itemprop="name" content="{username}'s Netlify Sites">
    <meta itemprop="image" content="{meta_image}">
    <meta property="og:title" content="{username}'s Netlify Sites">
    <meta property="og:image" content="{avatar}">
    <meta property="og:type" content="website">
    <meta name="twitter:title" content="{username}'s Netlify Sites">
    <meta name="twitter:image" content="{meta_image}">
    <meta name="twitter:card" content="summary_large_image">

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }}

        :root {{
            --github-bg: #ffffff;
            --github-text: #24292f;
            --github-text-secondary: #57606a;
            --github-border: #d0d7de;
            --github-primary: #0969da;
            --github-green: #1a7f37;
            --github-repo-bg: #ffffff;
            --github-hover: #f6f8fa;
            --github-shadow: rgba(140, 149, 159, 0.15);
            --netlify-primary: #00c7b7;
            --netlify-secondary: #32e6e2;
        }}

        body {{
            background-color: var(--github-bg);
            color: var(--github-text);
            line-height: 1.5;
            padding: 24px;
        }}

        .container {{
            max-width: 1280px;
            margin: 0 auto;
        }}

        /* Repository Header */
        .repo-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid var(--github-border);
            flex-wrap: wrap;
            gap: 16px;
        }}

        .repo-header h1 {{
            font-size: 32px;
            font-weight: 600;
            color: var(--github-text);
        }}

        .search-container {{
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: nowrap;
        }}

        .repo-search {{
            background-color: var(--github-bg);
            border: 1px solid var(--github-border);
            border-radius: 6px;
            padding: 10px 12px;
            color: var(--github-text);
            font-size: 14px;
            width: 300px;
            transition: all 0.2s;
            box-shadow: 0 1px 0 rgba(27, 31, 35, 0.04);
            flex-shrink: 0;
        }}

        .repo-search:focus {{
            outline: none;
            border-color: var(--github-primary);
            box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.15);
        }}

        .view-controls {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex: 1;
            justify-content: flex-end;
        }}

        .sort-buttons {{
            display: flex;
            gap: 4px;
            align-items: center;
            flex-shrink: 0;
        }}

        .view-toggle {{
            display: flex;
            gap: 4px;
            align-items: center;
            flex-shrink: 0;
        }}

        .btn-icon {{
            background: none;
            border: 1px solid var(--github-border);
            border-radius: 6px;
            padding: 8px 12px;
            cursor: pointer;
            color: var(--github-text-secondary);
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            background-color: var(--github-bg);
            white-space: nowrap;
        }}

        .btn-icon:hover {{
            background-color: var(--github-hover);
            border-color: var(--github-primary);
            color: var(--github-primary);
        }}

        .btn-icon.active {{
            background-color: var(--github-primary);
            border-color: var(--github-primary);
            color: white;
        }}

        .btn-icon i {{
            font-size: 14px;
        }}

        @media (max-width: 900px) {{
            .sort-text {{
                display: none;
            }}
            .btn-icon {{
                padding: 8px;
            }}
        }}

        @media (max-width: 700px) {{
            .search-container {{
                flex-wrap: wrap;
            }}
            .repo-search {{
                width: 100%;
            }}
            .view-controls {{
                width: 100%;
                justify-content: space-between;
            }}
        }}

        .user-info {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }}

        .user-details {{
            display: flex;
            flex-direction: row;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .user-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 1px solid var(--github-border);
            flex-shrink: 0;
        }}

        .user-name {{
            font-weight: 600;
            font-size: 18px;
            line-height: 1.2;
        }}

        .repo-count {{
            font-size: 14px;
            color: var(--github-text-secondary);
            background-color: var(--github-hover);
            padding: 2px 12px;
            border-radius: 12px;
            display: inline-block;
            align-self: flex-start;
        }}

        /* Screenshot Container */
        .screenshot-container {{
            width: 100%;
            height: 160px;
            overflow: hidden;
            border-radius: 6px 6px 0 0;
            background: linear-gradient(45deg, #f3f4f6, #e5e7eb);
            position: relative;
            cursor: pointer;
        }}

        .screenshot {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}

        .repo-item:hover .screenshot {{
            transform: scale(1.05);
        }}

        .screenshot-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
            color: white;
            font-size: 1em;
            font-weight: bold;
        }}

        .screenshot-container:hover .screenshot-overlay {{
            opacity: 1;
        }}

        /* Repository Grid */
        .repo-grid {{
            display: grid;
            gap: 20px;
            margin-bottom: 40px;
            transition: all 0.3s ease;
        }}

        .repo-grid.grid-view {{
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
        }}

        .repo-grid.list-view {{
            grid-template-columns: 1fr;
        }}

        /* Repository Item - Grid View */
        .repo-grid.grid-view .repo-item {{
            padding: 0 0 6px 0;
            flex-direction: column;
            overflow: hidden;
        }}

        .repo-grid.grid-view .repo-content {{
            padding: 16px 20px 20px 20px;
        }}

        .repo-grid.grid-view .repo-meta {{
            flex-wrap: wrap;
            padding: 0 20px 0 20px;
        }}

        /* Repository Item - List View */
        .repo-grid.list-view .repo-item {{
            padding: 0;
            display: flex;
            flex-direction: row;
            overflow: hidden;
        }}

        .repo-grid.list-view .screenshot-container {{
            width: 240px;
            height: 180px;
            flex-shrink: 0;
            border-radius: 6px 0 0 6px;
        }}

        .repo-grid.list-view .repo-content {{
            padding: 16px 6px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }}

        .repo-grid.list-view .repo-title {{
            margin-bottom: 8px;
        }}

        .repo-grid.list-view .site-details {{
            margin: 8px 0 !important;
        }}

        .repo-grid.list-view .repo-meta {{
            margin-top: auto;
            padding: 0;
        }}

        @media (max-width: 900px) {{
            .repo-grid.list-view .repo-item {{
                flex-direction: column;
            }}
            .repo-grid.list-view .screenshot-container {{
                width: 100%;
                height: 160px;
                border-radius: 6px 6px 0 0;
            }}
        }}

        /* Repository Item */
        .repo-item {{
            border: 1px solid var(--github-border);
            border-radius: 8px;
            background-color: var(--github-repo-bg);
            transition: all 0.2s;
            display: flex;
            height: 100%;
            box-shadow: 0 1px 3px var(--github-shadow);
        }}

        .repo-item:hover {{
            border-color: var(--github-primary);
            box-shadow: 0 3px 6px var(--github-shadow);
            transform: translateY(-2px);
        }}

        .repo-title {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 12px;
        }}

        .repo-title a {{
            color: var(--github-primary);
            text-decoration: none;
            font-size: 18px;
            font-weight: 600;
            line-height: 1.3;
            flex: 1;
            word-break: break-all;
        }}

        .repo-title a:hover {{
            text-decoration: underline;
        }}

        .repo-visibility {{
            border: 1px solid var(--github-border);
            border-radius: 12px;
            padding: 2px 8px;
            font-size: 11px;
            color: var(--github-text-secondary);
            text-transform: capitalize;
            font-weight: 500;
            margin-left: 8px;
            flex-shrink: 0;
        }}

        .repo-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            font-size: 12px;
            color: var(--github-text-secondary);
            margin-top: 12px;
            align-items: center;
            border-top: 1px solid var(--github-border);
            padding-top: 12px;
        }}

        .deploy-status {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .deploy-status i {{
            font-size: 12px;
        }}

        .repo-updated {{
            font-size: 12px;
            color: var(--github-text-secondary);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding-top: 32px;
            margin-top: 32px;
            border-top: 1px solid var(--github-border);
            color: var(--github-text-secondary);
            font-size: 14px;
        }}

        .footer a {{
            color: var(--github-primary);
            text-decoration: none;
        }}

        .footer a:hover {{
            text-decoration: underline;
        }}

        /* Loading & Error States */
        .loading,
        .error {{
            text-align: center;
            padding: 60px 20px;
            border-radius: 8px;
            background-color: var(--github-hover);
            border: 1px solid var(--github-border);
            grid-column: 1 / -1;
        }}

        .loading i {{
            font-size: 32px;
            margin-bottom: 16px;
            color: var(--github-primary);
        }}

        .loading p {{
            font-size: 16px;
            color: var(--github-text-secondary);
        }}

        .error {{
            color: #cf222e;
        }}

        .error i {{
            font-size: 32px;
            margin-bottom: 16px;
        }}

        /* No Results */
        .no-results {{
            text-align: center;
            padding: 60px 20px;
            border-radius: 8px;
            background-color: var(--github-hover);
            border: 1px solid var(--github-border);
            grid-column: 1 / -1;
        }}

        .no-results i {{
            font-size: 32px;
            margin-bottom: 16px;
            color: var(--github-text-secondary);
        }}

        .no-results p {{
            font-size: 16px;
            color: var(--github-text-secondary);
        }}

        /* API Info */
        .api-info {{
            font-size: 12px;
            color: var(--github-text-secondary);
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .api-info i {{
            color: var(--netlify-primary);
        }}

        /* Responsive Design */
        @media (max-width: 768px) {{
            body {{
                padding: 16px;
            }}

            .repo-header {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .search-container {{
                width: 100%;
                flex-direction: column;
                align-items: stretch;
            }}

            .repo-search {{
                width: 100%;
            }}

            .view-controls {{
                justify-content: space-between;
            }}

            .repo-grid.grid-view {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>

<body>
    <div class="container">
        <!-- Repository Header -->
        <div class="repo-header">
            <div>
                <div class="user-info">
                    <a href="{profile_url}" target="_blank" rel="noopener noreferrer">
                        <img src="{avatar}" class="user-avatar" alt="Avatar" onerror="this.src='https://www.netlify.com/img/press/logomark.png'">
                    </a>
                    <div class="user-details">
                        <a href="{profile_url}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; color: inherit;">
                            <div class="user-name" id="userName">{username}</div>
                        </a>
                        <div class="repo-count" id="repoCount">{site_count} sites</div>
                    </div>
                    <div class="api-info">
                        <i class="fas fa-cloud"></i>
                        <span>Live data from Netlify API</span>
                    </div>
                </div>
            </div>

            <div class="search-container">
                <input type="text" class="repo-search" placeholder="Find a site..." id="siteSearch">

                <div class="view-controls">
                    <div class="sort-buttons">
                        <button class="btn-icon" id="sortTimeBtn" title="Sort by last updated">
                            <i class="fas fa-clock"></i>
                            <span class="sort-text">Updated</span>
                        </button>
                        <button class="btn-icon" id="sortNameBtn" title="Sort by name">
                            <i class="fas fa-font"></i>
                            <span class="sort-text">Name</span>
                        </button>
                    </div>

                    <div class="view-toggle">
                        <button class="btn-icon" id="gridViewBtn" title="Grid view">
                            <i class="fas fa-th-large"></i>
                        </button>
                        <button class="btn-icon" id="listViewBtn" title="List view">
                            <i class="fas fa-list"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Repository Grid -->
        <div class="repo-grid grid-view" id="sitesContainer">
            {site_cards}
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Netlify Sites Dashboard | <a href="https://app.netlify.com" target="_blank">app.netlify.com</a></p>
            <p>Generated on {generated_date}</p>
        </div>
    </div>

    <script>
        // Site data
        const sitesData = {sites_json};
        
        // State management
        let currentSites = [...sitesData];
        let currentSort = localStorage.getItem('netlifySort') || 'time';
        let currentView = localStorage.getItem('netlifyView') || 'grid';
        let currentSearchQuery = '';

        // Format date to relative time
        function formatDate(dateString) {{
            if (!dateString) return "N/A";
            try {{
                const date = new Date(dateString);
                const now = new Date();
                const diffInSeconds = Math.floor((now - date) / 1000);

                if (diffInSeconds < 60) {{
                    return "just now";
                }} else if (diffInSeconds < 3600) {{
                    const minutes = Math.floor(diffInSeconds / 60);
                    return `${{minutes}} minute${{minutes > 1 ? 's' : ''}} ago`;
                }} else if (diffInSeconds < 86400) {{
                    const hours = Math.floor(diffInSeconds / 3600);
                    return `${{hours}} hour${{hours > 1 ? 's' : ''}} ago`;
                }} else if (diffInSeconds < 604800) {{
                    const days = Math.floor(diffInSeconds / 86400);
                    if (days === 1) return "yesterday";
                    return `${{days}} days ago`;
                }} else if (diffInSeconds < 2592000) {{
                    const weeks = Math.floor(diffInSeconds / 604800);
                    return `${{weeks}} week${{weeks > 1 ? 's' : ''}} ago`;
                }} else if (diffInSeconds < 31536000) {{
                    const months = Math.floor(diffInSeconds / 2592000);
                    return `${{months}} month${{months > 1 ? 's' : ''}} ago`;
                }} else {{
                    const years = Math.floor(diffInSeconds / 31536000);
                    return `${{years}} year${{years > 1 ? 's' : ''}} ago`;
                }}
            }} catch (e) {{
                return dateString;
            }}
        }}

        // Sort sites
        function sortSites(sites, sortType) {{
            const sorted = [...sites];
            switch (sortType) {{
                case 'name':
                    return sorted.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
                case 'time':
                default:
                    return sorted.sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at));
            }}
        }}

        // Search sites
        function searchSites(sites, query) {{
            if (!query.trim()) return sites;
            const searchTerms = query.toLowerCase().split(' ');
            return sites.filter(site => {{
                const siteText = `
                    ${{site.name.toLowerCase()}}
                    ${{site.custom_domain ? site.custom_domain.toLowerCase() : ''}}
                    ${{site.url ? site.url.toLowerCase() : ''}}
                    ${{site.account_name ? site.account_name.toLowerCase() : ''}}
                `;
                return searchTerms.every(term => siteText.includes(term));
            }});
        }}

        // Update view buttons active state
        function updateViewButtons() {{
            const gridBtn = document.getElementById('gridViewBtn');
            const listBtn = document.getElementById('listViewBtn');
            gridBtn.classList.toggle('active', currentView === 'grid');
            listBtn.classList.toggle('active', currentView === 'list');
        }}

        // Update sort buttons active state
        function updateSortButtons() {{
            const sortTimeBtn = document.getElementById('sortTimeBtn');
            const sortNameBtn = document.getElementById('sortNameBtn');
            sortTimeBtn.classList.toggle('active', currentSort === 'time');
            sortNameBtn.classList.toggle('active', currentSort === 'name');
        }}

        // Apply view to container
        function applyView() {{
            const container = document.getElementById('sitesContainer');
            container.classList.toggle('grid-view', currentView === 'grid');
            container.classList.toggle('list-view', currentView === 'list');
        }}

        // Render sites
        function renderSites(sites) {{
            const container = document.getElementById('sitesContainer');
            const repoCount = document.getElementById('repoCount');

            if (!sites || sites.length === 0) {{
                container.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <p>No sites found matching your search.</p>
                    </div>
                `;
                repoCount.textContent = '0 sites';
                return;
            }}

            repoCount.textContent = `${{sites.length}} site${{sites.length > 1 ? 's' : ''}}`;

            let html = '';
            sites.forEach(site => {{
                const siteUrl = site.url || null;
                const screenshotUrl = siteUrl ? `https://img.sdappnet.cloud/?url=${{siteUrl.replace('https://', '').replace('http://', '').split('/')[0]}}&w=1920&h=1080` : null;
                const siteName = site.name || 'Unnamed Site';
                const customDomain = site.custom_domain || 'No custom domain';
                const accountName = site.account_name || site.account_slug || '{username}';
                const visibility = site.plan === 'free' ? 'public' : 'private';
                const sslEnabled = site.ssl || false;
                const updatedAt = site.updated_at || site.created_at || '';

                html += `
                    <div class="repo-item">
                        <div class="screenshot-container" onclick="window.open('${{siteUrl || '#'}}', '_blank')">
                            <img class="screenshot" src="${{screenshotUrl || 'https://via.placeholder.com/600x400?text=No+Screenshot'}}" 
                                 alt="Screenshot of ${{siteName}}"
                                 onerror="this.src='https://via.placeholder.com/600x400?text=Failed+to+load'">
                            <div class="screenshot-overlay">
                                <i class="fas fa-external-link-alt"></i> Open site
                            </div>
                        </div>
                        <div class="repo-content">
                            <div class="repo-title">
                                <a href="${{siteUrl || '#'}}" target="_blank">${{siteName}}</a>
                                <span class="repo-visibility">${{visibility}}</span>
                            </div>
                            
                            <div class="site-details" style="margin: 12px 0; color: var(--github-text-secondary); font-size: 13px;">
                                <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-globe" style="width: 16px; color: var(--github-primary);"></i>
                                    <span>${{customDomain}}</span>
                                </div>
                                <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-link" style="width: 16px; color: var(--github-green);"></i>
                                    <span>${{siteUrl || 'No URL'}}</span>
                                </div>
                                <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-users" style="width: 16px; color: var(--github-text-secondary);"></i>
                                    <span>${{accountName}}</span>
                                </div>
                                ${{site.repo_url ? `
                                <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-code-branch" style="width: 16px; color: #f1e05a;"></i>
                                    <span>${{site.repo_url}} (${{site.repo_branch || 'main'}})</span>
                                </div>
                                ` : ''}}
                            </div>
                            
                            <div class="repo-meta">
                                <div class="deploy-status">
                                    <i class="fas fa-check-circle" style="color: ${{sslEnabled ? 'var(--github-green)' : '#ef4444'}};"></i>
                                    <span>SSL ${{sslEnabled ? 'Enabled' : 'Disabled'}}</span>
                                </div>
                                <div class="repo-updated">
                                    <span>Updated ${{formatDate(updatedAt)}}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }});

            container.innerHTML = html;
            applyView();
        }}

        // Update and render with current state
        function updateAndRender() {{
            let filteredSites = searchSites(currentSites, currentSearchQuery);
            filteredSites = sortSites(filteredSites, currentSort);
            renderSites(filteredSites);
            updateSortButtons();
        }}

        // Setup event listeners
        function setupControls() {{
            const searchInput = document.getElementById('siteSearch');
            const sortTimeBtn = document.getElementById('sortTimeBtn');
            const sortNameBtn = document.getElementById('sortNameBtn');
            const gridViewBtn = document.getElementById('gridViewBtn');
            const listViewBtn = document.getElementById('listViewBtn');

            searchInput.addEventListener('input', (e) => {{
                currentSearchQuery = e.target.value;
                updateAndRender();
            }});

            sortTimeBtn.addEventListener('click', () => {{
                currentSort = 'time';
                localStorage.setItem('netlifySort', 'time');
                updateAndRender();
            }});

            sortNameBtn.addEventListener('click', () => {{
                currentSort = 'name';
                localStorage.setItem('netlifySort', 'name');
                updateAndRender();
            }});

            gridViewBtn.addEventListener('click', () => {{
                currentView = 'grid';
                localStorage.setItem('netlifyView', 'grid');
                updateViewButtons();
                applyView();
            }});

            listViewBtn.addEventListener('click', () => {{
                currentView = 'list';
                localStorage.setItem('netlifyView', 'list');
                updateViewButtons();
                applyView();
            }});

            updateViewButtons();
            updateSortButtons();
            applyView();
        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            renderSites(currentSites);
            setupControls();
            document.getElementById('siteSearch').focus();
        }});
    </script>
</body>

</html>"""
    
    # Fill the template
    html_content = html_template.format(
        username=settings['username'],
        avatar=settings['avatar'],
        profile_url=settings['profile_url'],
        site_count=len(sites),
        site_cards=site_cards_html,
        generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sites_json=json.dumps(sites_data),
        meta_image=meta_image  # Add this line
    )
    
    return html_content

def save_html_file(html_content, output_file="index.html", output_dir=None):
    """Save HTML content to file, optionally in a specified directory"""
    try:
        # Handle directory if specified
        if output_dir:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            # Join directory and filename
            output_path = os.path.join(output_dir, output_file)
        else:
            output_path = output_file
        
        # Write the file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print_color(f"✅ HTML file saved as: {output_path}", Colors.GREEN)
        return True
        
    except Exception as e:
        print_color(f"❌ Error saving HTML file: {e}", Colors.RED)
        return False

def open_html_file(output_file="index.html", output_dir=None):
    """Open the HTML file in default browser"""
    try:
        # Construct the full path
        if output_dir:
            file_path = os.path.abspath(os.path.join(output_dir, output_file))
        else:
            file_path = os.path.abspath(output_file)
            
        webbrowser.open(f"file://{file_path}")
        print_color(f"✅ Opened {file_path} in your browser", Colors.GREEN)
        return True
    except Exception as e:
        print_color(f"❌ Error opening HTML file: {e}", Colors.RED)
        return False

def main():
    """Main function"""
    # Show interactive settings menu
    settings = show_settings_menu()
    
    # Initialize client with token from settings
    client = init_client(settings['token'])
    if not client:
        return
    
    # Fetch sites
    sites = fetch_all_sites(client)
    
    if not sites:
        print_color("❌ No sites found or error fetching sites", Colors.RED)
        return
    
    print_color(f"\n📊 Processing {len(sites)} sites...", Colors.BLUE)
    
    # Generate HTML grid
    print_color("🎨 Generating GitHub-style HTML grid view...", Colors.BLUE)
    html_content = generate_html_grid(sites, settings)
    
    # Save HTML file
    if save_html_file(html_content, OUTPUT_FILE, OUTPUT_DIRECTORY):
        print_color("\n📊 HTML Grid Summary:", Colors.BOLD)
        print_color(f"   Total sites: {len(sites)}", Colors.CYAN)
        print_color(f"   Output file: {OUTPUT_FILE}", Colors.CYAN)  # Changed output_file to OUTPUT_FILE
        print_color(f"   Username: {settings['username']}", Colors.CYAN)
        
        # Ask if user wants to open the file
        response = input(f"\n{Colors.BOLD}Open HTML file in browser? (y/n): {Colors.END}").lower()
        if response == 'y':
            open_html_file(OUTPUT_FILE, OUTPUT_DIRECTORY)  # Pass both filename and directory

    print_color("\n✨ Done! The GitHub-style HTML grid view has been generated.", Colors.GREEN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_color("\n\n👋 Operation cancelled by user.", Colors.BLUE)
    except Exception as e:
        print_color(f"\n❌ Unexpected error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()