import logging
import asyncio
import socket

from ping3 import ping

#for configurtaion
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

#checks if devices are reachable
async def isDeviceOnline(host_ip: str) -> str:
    eventLoop = asyncio.get_running_loop()
    try:
        target_IP = await eventLoop.run_in_executor(None, socket.gethostbyname, host_ip)
    except socket.gaierror:
        logger.error(f"Invalid IP format or unresolvable hostname: {host_ip}")
        return f"Invalid IP format or unresolvable hostname: `{host_ip}`"
    try:
        delay = await eventLoop.run_in_executor(None, lambda: ping(target_IP, timeout=2))
        if delay is None:
            logger.info(f"Host {host_ip} ({target_IP}) is unreachable.")
            return f" Host `{host_ip}` is **unreachable** (Request Timed Out)."
        elif delay is False:
            logger.info(f"Host {host_ip} ({target_IP}) returned an error on ping.")
            return f" Host `{host_ip}` is **unreachable** (Host Unknown/Error)."
        else:
            responseTime = round(delay * 1000, 2)
            logger.info(f"Host {host_ip} ({target_IP}) reachable. Time: {responseTime} ms.")
            return f"✅ Host `{host_ip}` is **reachable**.\n⏱ Response time: `{responseTime} ms`"
            
    except PermissionError:
        logger.error("Permission error: root privileges required for ping3.")
        return "⚠️ **Configuration Error**: `ping3` requires administrator/root privileges to run on macOS/Linux natively."
    except Exception as e:
        logger.error(f"Unexpected error when pinging {host_ip}: {e}")
        return f"⚠️ An unexpected error occurred: `{e}`"

# Predefined devices
DEVICE_LIST = {
    "Core Router": "192.168.1.1",
    "User Phone": "192.168.1.4"
}

#check all devices status 
async def getAllStatues() -> str:
    logger.info("Initiating reachability check for all predefined devices.")
    eventLoop = asyncio.get_running_loop()
    
    results = [" **Network Devices Status:**\n"]
    
    for name, host_ip in DEVICE_LIST.items():
        try:
            target_IP = await eventLoop.run_in_executor(None, socket.gethostbyname, host_ip)
            delay = await eventLoop.run_in_executor(None, lambda: ping(target_IP, timeout=1))
            if delay is None or delay is False:
                results.append(f" **{name}** (`{host_ip}`) - DOWN")
            else:
                responseTime = round(delay * 1000, 2)
                results.append(f"✅ **{name}** (`{host_ip}`) - UP ({responseTime} ms)")
        except socket.gaierror:
            results.append(f"⚠️ **{name}** (`{host_ip}`) - INVALID IP")
        except PermissionError:
            results.append(f"⚠️ **{name}** (`{host_ip}`) - PERMISSION ERROR")
        except Exception:
            results.append(f"⚠️ **{name}** (`{host_ip}`) - ERROR")

    return "\n".join(results)

# for traceroute to the specified IP
async def findPath(host_ip: str) -> str:
    eventLoop = asyncio.get_running_loop()
    try:
        target_IP = await eventLoop.run_in_executor(None, socket.gethostbyname, host_ip)
    except socket.gaierror:
        logger.error(f"Invalid IP format or unresolvable hostname: {host_ip}")
        return f" Invalid IP format or unresolvable hostname: `{host_ip}`"

    try:
        process = await asyncio.create_subprocess_exec(
            'traceroute', '-m', '15', '-w', '1', '-q', '1', target_IP,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            process.kill()
            return f"⚠️ Traceroute to `{host_ip}` timed out after 30 seconds."

        if stdout:
            output = stdout.decode('utf-8').strip()
            return f" **Traceroute to `{host_ip}`**:\n```text\n{output}\n```"
        
        if stderr:
            error_output = stderr.decode('utf-8').strip()
            return f"⚠️ **Traceroute Error**: `{error_output}`"
            
    except Exception as e:
        logger.error(f"Unexpected error when tracing {host_ip}: {e}")
        return f"⚠️ An unexpected error occurred: `{e}`"
        
    return f"⚠️ Traceroute to `{host_ip}` failed to produce output."

#traceroute if the device is down or has high latency every 150ms
async def deviceHealth(name: str, host_ip: str):
    logger.info(f"Evaluating health for {name} ({host_ip})")
    eventLoop = asyncio.get_running_loop()
    
    try:
        target_IP = await eventLoop.run_in_executor(None, socket.gethostbyname, host_ip)
        delay = await eventLoop.run_in_executor(None, lambda: ping(target_IP, timeout=2))
        
        if delay is None or delay is False:
            logger.warning(f"Device {name} is DOWN. Initiating trace...")
            trace_result = await findPath(target_IP)
            return (f"🚨 **ALERT: DEVICE DOWN / ROUTE FAILURE** 🚨\n"
                    f"**Device:** {name} (`{host_ip}`)\n"
                    f"**Reason:** Ping failed or request timed out.\n\n"
                    f"**Route Diagnostics:**\n{trace_result}")
        
        responseTime = round(delay * 1000, 2)
        if responseTime > 150.0:
            logger.warning(f"Device {name} has HIGH LATENCY. Initiating trace...")
            trace_result = await findPath(target_IP)
            return (f"⚠️ **ALERT: HIGH LATENCY** ⚠️\n"
                    f"**Device:** {name} (`{host_ip}`)\n"
                    f"**Response Time:** {responseTime} ms\n"
                    f"**Route Diagnostics:**\n{trace_result}")
            
    except socket.gaierror:
        return f"⚠️ **ALERT: DNS ERROR** ⚠️\n**Device:** {name} (`{host_ip}`) cannot be resolved."
    except PermissionError:
        return None 
    except Exception as e:
        logger.error(f"Error evaluating health for {name}: {e}")
        return f"⚠️ **ALERT: HEALTH CHECK ERROR** ⚠️\n**Device:** {name} (`{host_ip}`)\n**Error:** `{e}`"
        
    return None 
