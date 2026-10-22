import io
import os
import shutil
import sys
import urllib.error
import urllib.request
import zipfile

def download_repo(user, repo, dest_dir):
    urls = [
        f"https://github.com/{user}/{repo}/archive/refs/heads/main.zip",
        f"https://github.com/{user}/{repo}/archive/refs/heads/master.zip",
        f"https://github.com/{user}/{repo}/archive/HEAD.zip",
    ]

    zip_bytes = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Polyglot"})
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    zip_bytes = resp.read()
                    break
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            continue

    if zip_bytes is None:
        return False

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        members = archive.infolist()
        if not members:
            return False

        root_prefix = members[0].filename.split("/")[0] + "/"

        for member in members:
            if not member.filename.startswith(root_prefix):
                continue
            rel_path = member.filename[len(root_prefix):]
            if not rel_path:
                continue

            target_path = os.path.join(dest_dir, rel_path)
            if member.is_dir():
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with archive.open(member) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    return True

def install_extension(shortlink, modules_dir):
    if "/" not in shortlink:
        return False

    user, repo = shortlink.split("/", 1)
    short_name = repo[:-4] if repo.endswith(".lua") else repo

    primary_dir = os.path.join(modules_dir, short_name)
    if os.path.exists(primary_dir) and os.listdir(primary_dir):
        return True

    temp_dir = os.path.join(modules_dir, f".tmp_{short_name}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    success = download_repo(user, repo, temp_dir)
    if not success:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False

    if os.path.exists(primary_dir):
        shutil.rmtree(primary_dir, ignore_errors=True)
    os.rename(temp_dir, primary_dir)

    if short_name != repo:
        alias_dir = os.path.join(modules_dir, repo)
        if not os.path.exists(alias_dir):
            try:
                shutil.copytree(primary_dir, alias_dir)
            except OSError:
                pass

    return True

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    allow_offline = False
    args = sys.argv[1:]
    if "--allow-offline" in args:
        allow_offline = True
        args.remove("--allow-offline")

    if not args:
        sys.exit(1)

    modules_dir = os.path.abspath(args[0])
    os.makedirs(modules_dir, exist_ok=True)
    extensions = args[1:]

    overall_success = True
    for ext in extensions:
        if not ext.strip():
            continue
        ok = install_extension(ext.strip(), modules_dir)
        if not ok:
            print(f"Warning: Failed to install Lua extension {ext.strip()}")
            overall_success = False

    if not overall_success and not allow_offline:
        sys.exit(1)

if __name__ == "__main__":
    main()
