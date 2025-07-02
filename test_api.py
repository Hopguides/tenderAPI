#!/usr/bin/env python3
"""
Avtomatizirani test skript za Tender API
Testira vse platforme in funkcionalnosti
"""

import asyncio
import httpx
import json
import sys
import time
from typing import Dict, Any

# Test konfiguracija
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class TenderAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        
    async def run_all_tests(self):
        """Zaženi vse teste"""
        print("🧪 TENDER API AVTOMATIZIRANI TESTI 🧪")
        print("=" * 60)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test 1: Osnovni endpoints
            await self.test_basic_endpoints(client)
            
            # Test 2: Platform info
            await self.test_platform_info(client)
            
            # Test 3: Health check
            await self.test_health_check(client)
            
            # Test 4: Platform searches
            await self.test_platform_searches(client)
            
            # Test 5: Multi-platform search
            await self.test_multi_platform_search(client)
            
            # Test 6: Error handling
            await self.test_error_handling(client)
        
        # Poročilo
        self.print_summary()
    
    async def test_basic_endpoints(self, client: httpx.AsyncClient):
        """Test osnovnih endpoints"""
        print("\n📋 Test 1: Osnovni endpoints")
        
        # Root endpoint
        success = await self.make_test_request(
            client, "GET", "/", 
            "Root endpoint", 
            expected_keys=["name", "version", "platforms"]
        )
        
        # OpenAPI docs
        success = await self.make_test_request(
            client, "GET", "/openapi.json",
            "OpenAPI schema",
            expected_keys=["openapi", "info", "paths"]
        )
    
    async def test_platform_info(self, client: httpx.AsyncClient):
        """Test platform informacij"""
        print("\n🔧 Test 2: Platform informacije")
        
        response = await self.make_test_request(
            client, "GET", "/platforms",
            "Platform info",
            expected_keys=["bonfire", "sam", "ted"]
        )
        
        if response:
            # Preveri Bonfire platform specifike
            bonfire_info = response.get("bonfire", {})
            if bonfire_info.get("name") == "Bonfire":
                self.log_success("Bonfire platform pravilno konfiguriran")
            else:
                self.log_error("Bonfire platform ni pravilno konfiguriran")
    
    async def test_health_check(self, client: httpx.AsyncClient):
        """Test health check"""
        print("\n💚 Test 3: Health check")
        
        response = await self.make_test_request(
            client, "GET", "/health",
            "Health check",
            expected_keys=["status", "platforms", "registered_platforms"]
        )
        
        if response:
            if response.get("status") == "healthy":
                self.log_success("Sistem je zdrav")
            else:
                self.log_error(f"Sistem ni zdrav: {response.get('status')}")
            
            platforms = response.get("platforms", {})
            for platform, status in platforms.items():
                if status in ["available", "configured"]:
                    self.log_success(f"Platform {platform}: {status}")
                else:
                    self.log_warning(f"Platform {platform}: {status}")
    
    async def test_platform_searches(self, client: httpx.AsyncClient):
        """Test iskanja po platformah"""
        print("\n🔍 Test 4: Platform searches")
        
        # Test Bonfire search
        bonfire_data = {
            "organization": "california",
            "keywords": "IT services",
            "limit": 2,
            "status": "all"
        }
        
        await self.make_test_request(
            client, "POST", "/search/bonfire",
            "Bonfire search",
            json_data=bonfire_data,
            expected_keys=["platform", "total_count", "results", "query_info"]
        )
        
        # Test TED search (brez API ključa)
        ted_data = {
            "query": "software",
            "limit": 2
        }
        
        await self.make_test_request(
            client, "POST", "/search/ted",
            "TED search",
            json_data=ted_data,
            expected_keys=["platform", "total_count", "results"]
        )
        
        # Test SAM search (brez API ključa - pričakujemo napako)
        sam_data = {
            "posted_from": "01/01/2024",
            "posted_to": "01/31/2024",
            "limit": 2
        }
        
        await self.make_test_request(
            client, "POST", "/search/sam",
            "SAM search (brez API ključa)",
            json_data=sam_data,
            expected_keys=["platform", "total_count", "results"],
            expect_error=True
        )
    
    async def test_multi_platform_search(self, client: httpx.AsyncClient):
        """Test multi-platform search"""
        print("\n🌐 Test 5: Multi-platform search")
        
        search_data = {
            "bonfire": {
                "organization": "california",
                "keywords": "consulting",
                "limit": 1
            },
            "ted": {
                "query": "consulting",
                "limit": 1
            }
        }
        
        await self.make_test_request(
            client, "POST", "/search/all",
            "Multi-platform search",
            json_data=search_data,
            expected_keys=["results", "summary"]
        )
    
    async def test_error_handling(self, client: httpx.AsyncClient):
        """Test error handling"""
        print("\n❌ Test 6: Error handling")
        
        # Test neobstoječe platforme
        await self.make_test_request(
            client, "POST", "/search/nonexistent",
            "Neobstoječa platforma",
            json_data={"test": "data"},
            expect_error=True,
            expected_status=404
        )
        
        # Test napačnih podatkov
        await self.make_test_request(
            client, "POST", "/search/bonfire",
            "Napačni podatki za Bonfire",
            json_data={"invalid": "data"},
            expect_error=True,
            expected_status=422
        )
    
    async def make_test_request(self, client: httpx.AsyncClient, method: str, 
                              endpoint: str, description: str,
                              json_data: Dict = None, expected_keys: list = None,
                              expect_error: bool = False, expected_status: int = 200) -> Dict[str, Any]:
        """Naredi test request"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=json_data)
            else:
                raise ValueError(f"Nepodprt method: {method}")
            
            # Preveri status code
            if expect_error:
                if response.status_code >= 400:
                    self.log_success(f"{description}: Pričakovana napaka ({response.status_code})")
                else:
                    self.log_error(f"{description}: Pričakovali napako, dobili {response.status_code}")
                return None
            else:
                if response.status_code == expected_status:
                    self.log_success(f"{description}: Status {response.status_code} ✓")
                else:
                    self.log_error(f"{description}: Pričakovali {expected_status}, dobili {response.status_code}")
                    return None
            
            # Preveri JSON response
            try:
                data = response.json()
            except Exception as e:
                self.log_error(f"{description}: Napaka pri parsiranju JSON: {e}")
                return None
            
            # Preveri pričakovane ključe
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    self.log_warning(f"{description}: Manjkajo ključi: {missing_keys}")
                else:
                    self.log_success(f"{description}: Vsi pričakovani ključi prisotni ✓")
            
            return data
            
        except Exception as e:
            self.log_error(f"{description}: Napaka: {e}")
            return None
    
    def log_success(self, message: str):
        """Zabeleži uspeh"""
        print(f"  ✅ {message}")
        self.results.append(("SUCCESS", message))
    
    def log_error(self, message: str):
        """Zabeleži napako"""
        print(f"  ❌ {message}")
        self.results.append(("ERROR", message))
    
    def log_warning(self, message: str):
        """Zabeleži opozorilo"""
        print(f"  ⚠️  {message}")
        self.results.append(("WARNING", message))
    
    def print_summary(self):
        """Natisni povzetek"""
        print("\n" + "=" * 60)
        print("📊 POVZETEK TESTOV")
        print("=" * 60)
        
        success_count = len([r for r in self.results if r[0] == "SUCCESS"])
        error_count = len([r for r in self.results if r[0] == "ERROR"])
        warning_count = len([r for r in self.results if r[0] == "WARNING"])
        total_count = len(self.results)
        
        print(f"✅ Uspešni: {success_count}")
        print(f"❌ Napake: {error_count}")
        print(f"⚠️  Opozorila: {warning_count}")
        print(f"📊 Skupaj: {total_count}")
        
        if error_count == 0:
            print("\n🎉 VSI TESTI USPEŠNI!")
        elif error_count < 3:
            print("\n⚠️  VEČINA TESTOV USPEŠNIH")
        else:
            print("\n❌ VEČ NAPAK - PREVERI KONFIGURACIJO")
        
        # Natisni napake
        if error_count > 0:
            print("\n❌ NAPAKE:")
            for result_type, message in self.results:
                if result_type == "ERROR":
                    print(f"  • {message}")


async def main():
    """Glavna funkcija"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    print(f"🎯 Testiram API na: {base_url}")
    
    # Preveri če je server dostopen
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Server je dostopen")
            else:
                print(f"⚠️  Server vrača status {response.status_code}")
    except Exception as e:
        print(f"❌ Server ni dostopen: {e}")
        print("💡 Zaženi server z: uvicorn main:app --reload --port 8000")
        return
    
    # Zaženi teste
    tester = TenderAPITester(base_url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

