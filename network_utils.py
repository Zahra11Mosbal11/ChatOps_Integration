"""
network_utils.py
Contains logic for checking the reachability status of network devices.
Uses async/await execution for non-blocking operations.
"""
import asyncio
import socket
import logging
from ping3 import ping

# Set up logging for devsecops approach
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def check_device_status(ip: str) -> str:
    """
    Asynchronously checks if a given IP or hostname is reachable via ICMP ping.
    
    Args:
        ip (str): The IP address or hostname to check.
        
    Returns:
        str: A formatted report message for the user.
    """
    logger.info(f"Initiating reachability check for: {ip}")
    
    # 1. Input Validation: Check if it's a resolvable hostname/IP
    try:
        # socket.gethostbyname validates and resolves the IP
        resolved_ip = socket.gethostbyname(ip)
    except socket.gaierror:
        logger.error(f"Invalid IP format or unresolvable hostname: {ip}")
        return f"❌ Invalid IP format or unresolvable hostname: `{ip}`"

    # 2. Ping Check using thread pool
    # Since ping3's ping() is blocking, we use run_in_executor
    # to avoid freezing the Telegram bot's async event loop.
    loop = asyncio.get_running_loop()
    try:
        # Timeout is 2 seconds
        # run_in_executor runs the synchronous function in a separate thread
        delay = await loop.run_in_executor(None, lambda: ping(resolved_ip, timeout=2))
        
        if delay is None:
            logger.info(f"Host {ip} ({resolved_ip}) is unreachable.")
            return f"❌ Host `{ip}` is **unreachable** (Request Timed Out)."
        elif delay is False:
            logger.info(f"Host {ip} ({resolved_ip}) returned an error on ping.")
            return f"❌ Host `{ip}` is **unreachable** (Host Unknown/Error)."
        else:
            delay_ms = round(delay * 1000, 2)
            logger.info(f"Host {ip} ({resolved_ip}) reachable. Time: {delay_ms} ms.")
            return f"✅ Host `{ip}` is **reachable**.\n⏱ Response time: `{delay_ms} ms`"
            
    except PermissionError:
        logger.error("Permission error: root privileges required for ping3.")
        return "⚠️ **Configuration Error**: `ping3` requires administrator/root privileges to run on macOS/Linux natively."
    except Exception as e:
        logger.error(f"Unexpected error when pinging {ip}: {e}")
        return f"⚠️ An unexpected error occurred: `{e}`"

# Predefined devices dictionary for group monitoring
PREDEFINED_DEVICES = {
    "Core Router": "192.168.1.1",
    "Distribution Switch": "192.168.1.2",
    "DNS Server": "1.1.1.1",
    "Web Server": "8.8.8.8"
}

async def check_all_devices_status() -> str:
    """
    Concurrently checks the status of all predefined network devices.
    Returns a summarized report.
    """
    logger.info("Initiating reachability check for all predefined devices.")
    loop = asyncio.get_running_loop()
    
    report_lines = ["📊 **Predefined Network Devices Status:**\n"]
    
    # Check each device sequentially to avoid potential rate limit/socket issues
    # Note: Can be changed to asyncio.gather(...) for true parallel concurrency if list grows large
    for name, ip in PREDEFINED_DEVICES.items():
        try:
            resolved_ip = socket.gethostbyname(ip)
            # Use shorter timeout (1 sec) for bulk checks to keep response time fast
            delay = await loop.run_in_executor(None, lambda: ping(resolved_ip, timeout=1))
            
            if delay is None or delay is False:
                report_lines.append(f"🔴 **{name}** (`{ip}`) - DOWN")
            else:
                delay_ms = round(delay * 1000, 2)
                report_lines.append(f"🟢 **{name}** (`{ip}`) - UP ({delay_ms} ms)")
        except socket.gaierror:
            report_lines.append(f"⚠️ **{name}** (`{ip}`) - INVALID IP")
        except PermissionError:
            report_lines.append(f"⚠️ **{name}** (`{ip}`) - PERMISSION ERROR")
        except Exception:
            report_lines.append(f"⚠️ **{name}** (`{ip}`) - ERROR")

    return "\n".join(report_lines)

async def trace_route(ip: str) -> str:
    """
    Asynchronously performs a traceroute to the specified IP or hostname.
    Limits to 15 hops to avoid excessive wait times and text.
    """
    logger.info(f"Initiating traceroute to: {ip}")
    
    # 1. Input Validation: Check if it's a resolvable hostname/IP
    try:
        resolved_ip = socket.gethostbyname(ip)
    except socket.gaierror:
        logger.error(f"Invalid IP format or unresolvable hostname: {ip}")
        return f"❌ Invalid IP format or unresolvable hostname: `{ip}`"

    try:
        # Run the system shell traceroute command asynchronously
        # -m 15 limits the trace to 15 hops.
        # -w 1 limits the wait time for a hop to 1 second.
        # Note: 'traceroute' is the command on macOS/Linux.
        process = await asyncio.create_subprocess_exec(
            'traceroute', '-m', '15', '-w', '1', '-q', '1', resolved_ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for the command to complete, with a safety timeout (e.g., 30s)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            process.kill()
            return f"⚠️ Traceroute to `{ip}` timed out after 30 seconds."

        if stdout:
            output = stdout.decode('utf-8').strip()
            # Since the output can get long, we encompass it in a markdown code block
            return f"🗺 **Traceroute to `{ip}`**:\n```text\n{output}\n```"
        
        if stderr:
            error_output = stderr.decode('utf-8').strip()
            return f"⚠️ **Traceroute Error**: `{error_output}`"
            
    except Exception as e:
        logger.error(f"Unexpected error when tracing {ip}: {e}")
        return f"⚠️ An unexpected error occurred: `{e}`"
        
    return f"⚠️ Traceroute to `{ip}` failed to produce output."
