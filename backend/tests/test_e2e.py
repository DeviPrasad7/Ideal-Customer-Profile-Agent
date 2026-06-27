import asyncio
import httpx
import sys

API_URL = "http://localhost:8000"

async def test_e2e_workflow():
    print("Starting E2E workflow test...")
    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
        # 1. Check health
        try:
            resp = await client.get("/health")
            resp.raise_for_status()
            print("[OK] API is healthy")
        except Exception as e:
            print(f"[FAIL] API health check failed: {e}")
            sys.exit(1)

        # 2. Submit a prospect
        payload = {
            "company_name": "TestCorp Inc.",
            "website": "https://example.com",
            "trigger_event": "e2e_test",
            "simulate_failure": False
        }
        print("Submitting prospect...")
        resp = await client.post("/api/prospects", json=payload)
        if resp.status_code != 200:
            print(f"[FAIL] Failed to submit prospect: {resp.text}")
            sys.exit(1)
        
        data = resp.json()
        prospect_id = data.get("prospect_id")
        print(f"[OK] Submitted prospect: {prospect_id}")

        # 3. Poll for status
        print("Polling prospect status...")
        completed = False
        requires_hitl = False
        hitl_id = None
        
        for i in range(15):  # poll up to 15 times (approx 30s)
            resp = await client.get(f"/api/prospects/{prospect_id}")
            if resp.status_code == 200:
                p_data = resp.json()
                status = p_data.get("status")
                print(f"   Status: {status}")
                if status == "COMPLETED":
                    completed = True
                    break
                elif status == "REQUIRES_HITL":
                    requires_hitl = True
                    break
            await asyncio.sleep(2)
        
        if requires_hitl:
            print("[OK] Prospect requires HITL approval.")
            # Find the HITL request
            resp = await client.get("/api/hitl/pending")
            hitl_reqs = resp.json()
            for req in hitl_reqs:
                if req.get("prospect_id") == prospect_id:
                    hitl_id = req.get("id")
                    break
            
            if hitl_id:
                print(f"Approving HITL request {hitl_id}...")
                resp = await client.post(f"/api/hitl/{hitl_id}/approve")
                if resp.status_code == 200:
                    print("[OK] HITL Approved.")
                else:
                    print(f"[FAIL] HITL Approval failed: {resp.text}")
                    sys.exit(1)
                
                # Poll again until completed
                print("Polling for completion post-HITL...")
                for i in range(10):
                    resp = await client.get(f"/api/prospects/{prospect_id}")
                    if resp.status_code == 200:
                        status = resp.json().get("status")
                        print(f"   Status: {status}")
                        if status == "COMPLETED":
                            completed = True
                            break
                    await asyncio.sleep(2)
        
        if completed:
            print("[OK] E2E Test Passed. Prospect reached COMPLETED status.")
        else:
            print("[FAIL] E2E Test Failed. Prospect did not complete in time.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_e2e_workflow())
