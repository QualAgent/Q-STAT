
import asyncio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def run():
    # SSE 방식의 MCP 서버 연결 (Docker 내부에서 실행하므로 http://localhost:8000/sse 사용)
    # 만약 호스트에서 실행한다면 http://localhost:8200/sse (포트 매핑)
    
    # 지금은 "docker-compose run mcp python ..." 으로 실행할 것이므로
    # 같은 네트워크 안(localhost)의 8000 포트를 바라봐야 함.
    # 하지만 서버가 '이미 떠 있는 컨테이너'라면 주소가 다를 수 있음.
    
    # 1. 호스트에서 실행하는 시나리오 (외부 -> 컨테이너 8200)
    # url = "http://localhost:8200/sse"

    # 2. 컨테이너 내부에서 실행하는 시나리오 (내부 -> 내부 8000)
    # 우리가 `docker-compose run`으로 실행할 거라면 
    # 'qstat_mcp' 컨테이너의 8000 포트로 접속해야 함.
    
    # 간단히 호스트에서 테스트한다고 가정하고 url 설정 (windows)
    # 호스트 PC에서 실행하려면 python 환경이 필요함.
    
    # Docker 내부에서 실행하려면:
    # `docker-compose run --rm mcp python src/test_mcp_client.py` 
    # 이때는 `http://qstat_mcp:8000/sse` 로 접근해야 함 (서비스 이름 사용)
    
    url = "http://localhost:8000/sse" 

    print(f"Connecting to MCP Server at {url}...")
    try:
        async with sse_client(url=url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 도구 목록 조회
                result = await session.list_tools()
                
                print(f"\n[Success] Found {len(result.tools)} tools!")
                for tool in result.tools:
                    print(f"- {tool.name}: {tool.description}")

    except Exception as e:
        print(f"[Error] Failed to connect or list tools: {e}")

if __name__ == "__main__":
    asyncio.run(run())
