#!/usr/bin/env python3
"""
Firecrawl API Client Service
Clean, reusable client for Firecrawl Extract API operations
"""
import os
import asyncio
import aiohttp
import json
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv

from app_logging import get_logger
from core.config import Config

# Load environment variables
load_dotenv()


class FirecrawlError(Exception):
    """Custom exception for Firecrawl API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class FirecrawlClient:
    """
    Clean Firecrawl Extract API client
    Handles authentication, requests, retries, and error handling
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 120):
        """
        Initialize Firecrawl client
        
        Args:
            api_key: Firecrawl API key (defaults to environment variable)
            timeout: Request timeout in seconds
        """
        self.logger = get_logger('services.firecrawl_client')
        
        # API configuration
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment variables")
            
        self.base_url = "https://api.firecrawl.dev/v1"
        self.extract_url = f"{self.base_url}/extract"
        self.timeout = timeout
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting and retry configuration
        self.max_retries = Config.MAX_RETRIES
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        
        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'successful_extracts': 0,
            'failed_extracts': 0,
            'total_cost': 0.0,
            'total_processing_time': 0.0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is initialized"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _rate_limit(self):
        """Implement simple rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _resolve_redirect_url(self, url: str) -> str:
        """
        Resolve redirect URLs (especially Google redirects)
        
        Args:
            url: URL to resolve
            
        Returns:
            Resolved URL
        """
        if 'google.com/url' not in url:
            return url
            
        try:
            await self._ensure_session()
            
            async with self.session.get(
                url, 
                allow_redirects=True, 
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                final_url = str(response.url)
                
                # Manual parsing for stubborn Google redirects
                if 'google.com/url' in final_url:
                    parsed = urllib.parse.urlparse(url)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'url' in params:
                        final_url = params['url'][0]
                        self.logger.debug(f"Extracted URL from Google redirect: {final_url[:80]}...")
                        
                self.logger.debug(f"Resolved redirect: {url[:50]}... → {final_url[:50]}...")
                return final_url
                
        except Exception as e:
            self.logger.warning(f"Failed to resolve redirect {url}: {e}")
            return url
    
    async def _wait_for_job_completion(self, job_id: str, max_wait: int = None) -> Dict[str, Any]:
        """
        Wait for asynchronous Extract API job completion
        
        Args:
            job_id: Job ID from Extract API
            max_wait: Maximum wait time in seconds
            
        Returns:
            Extracted data
            
        Raises:
            FirecrawlError: If job fails or times out
        """
        max_wait = max_wait or self.timeout
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        start_time = time.time()
        check_count = 0
        check_interval = 5  # seconds
        
        while (time.time() - start_time) < max_wait:
            try:
                check_count += 1
                self.logger.debug(f"Checking job {job_id} status (attempt {check_count})...")
                
                await self._ensure_session()
                async with self.session.get(
                    f"{self.base_url}/extract/{job_id}",
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status')
                        
                        if status == 'completed':
                            extracted_data = data.get('data', [])
                            if isinstance(extracted_data, dict):
                                extracted_data = [extracted_data]
                            
                            if extracted_data:
                                self.logger.debug(f"Job {job_id} completed successfully")
                                return extracted_data[0]
                            else:
                                raise FirecrawlError(f"Job {job_id} completed but returned no data")
                                
                        elif status == 'failed':
                            error_msg = data.get('error', 'Unknown error')
                            raise FirecrawlError(f"Job {job_id} failed: {error_msg}")
                        
                        # Status is 'processing' - continue waiting
                        
                    else:
                        self.logger.warning(f"HTTP {response.status} when checking job {job_id}")
                        
            except FirecrawlError:
                raise  # Re-raise Firecrawl errors
            except Exception as e:
                self.logger.warning(f"Error checking job {job_id} status: {e}")
            
            await asyncio.sleep(check_interval)
        
        raise FirecrawlError(f"Job {job_id} timed out after {max_wait} seconds")
    
    async def extract_content(
        self, 
        url: str, 
        schema: Optional[Dict] = None,
        prompt: Optional[str] = None,
        resolve_redirects: bool = True
    ) -> Dict[str, Any]:
        """
        Extract content from a URL using Firecrawl Extract API
        
        Args:
            url: URL to extract content from
            schema: Optional JSON schema for structured extraction
            prompt: Optional prompt for extraction guidance
            resolve_redirects: Whether to resolve redirects before extraction
            
        Returns:
            Extracted content data
            
        Raises:
            FirecrawlError: If extraction fails
        """
        start_time = time.time()
        
        try:
            await self._ensure_session()
            await self._rate_limit()
            
            # Resolve redirects if requested
            if resolve_redirects:
                url = await self._resolve_redirect_url(url)
            
            # Prepare request payload
            payload = {
                'urls': [url]
            }
            
            # Add schema if provided
            if schema:
                payload['schema'] = schema
            elif Config.EXTRACT_SCHEMA:
                payload['schema'] = Config.EXTRACT_SCHEMA
            
            # Add prompt if provided
            if prompt:
                payload['prompt'] = prompt
            elif Config.EXTRACT_PROMPT:
                payload['prompt'] = Config.EXTRACT_PROMPT
            
            self.logger.debug(f"Sending Extract API request for: {url[:80]}...")
            
            # Make Extract API request
            async with self.session.post(
                self.extract_url,
                headers={'Content-Type': 'application/json'},
                json=payload
            ) as response:
                
                self.stats['total_requests'] += 1
                
                if response.status == 200:
                    # Synchronous response
                    result = await response.json()
                    
                    if result.get('success') and result.get('data'):
                        data = result.get('data', [])
                        if isinstance(data, dict):
                            data = [data]
                        if not data:
                            raise FirecrawlError("Extract API returned no data")
                        extracted = data[0]
                    elif result.get('id') and not result.get('data'):
                        # Asynchronous job - wait for completion
                        self.logger.debug(f"Started async job: {result['id']}")
                        extracted = await self._wait_for_job_completion(result['id'])
                    else:
                        raise FirecrawlError(f"Unexpected API response: {result}")
                        
                elif response.status == 202:
                    # Asynchronous job
                    result = await response.json()
                    job_id = result.get('id')
                    
                    if not job_id:
                        raise FirecrawlError("No job ID in 202 response")
                    
                    self.logger.debug(f"Started async job: {job_id}")
                    extracted = await self._wait_for_job_completion(job_id)
                    
                else:
                    error_text = await response.text()
                    raise FirecrawlError(
                        f"Extract API error {response.status}: {error_text}",
                        status_code=response.status
                    )
                
                # Update statistics
                processing_time = time.time() - start_time
                self.stats['successful_extracts'] += 1
                self.stats['total_cost'] += 0.005  # Estimated cost per request
                self.stats['total_processing_time'] += processing_time
                
                self.logger.debug(f"Successfully extracted content from {url[:60]}... in {processing_time:.1f}s")
                return extracted
                
        except FirecrawlError:
            self.stats['failed_extracts'] += 1
            raise
        except Exception as e:
            self.stats['failed_extracts'] += 1
            raise FirecrawlError(f"Extraction failed: {str(e)}")
    
    async def extract_with_retry(
        self, 
        url: str, 
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract content with automatic retries
        
        Args:
            url: URL to extract content from
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for extract_content
            
        Returns:
            Extracted content data
            
        Raises:
            FirecrawlError: If all retry attempts fail
        """
        max_retries = max_retries if max_retries is not None else self.max_retries
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{max_retries} for {url}")
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                
                return await self.extract_content(url, **kwargs)
                
            except FirecrawlError as e:
                last_error = e
                
                # Check for permanent errors that shouldn't be retried
                permanent_errors = ['403', 'blocked', 'not supported', 'Forbidden']
                if any(err in str(e) for err in permanent_errors):
                    self.logger.warning(f"Permanent error detected, skipping retries: {e}")
                    break
                
                if attempt < max_retries:
                    self.logger.warning(f"Extraction attempt {attempt + 1} failed: {e}")
                else:
                    self.logger.error(f"All {max_retries + 1} extraction attempts failed for {url}")
        
        raise last_error or FirecrawlError(f"Extraction failed after {max_retries + 1} attempts")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get client usage statistics
        
        Returns:
            Dictionary with usage statistics
        """
        total_requests = max(1, self.stats['total_requests'])
        
        return {
            'total_requests': self.stats['total_requests'],
            'successful_extracts': self.stats['successful_extracts'],
            'failed_extracts': self.stats['failed_extracts'],
            'success_rate_percent': (self.stats['successful_extracts'] / total_requests) * 100,
            'average_processing_time': self.stats['total_processing_time'] / max(1, self.stats['successful_extracts']),
            'estimated_total_cost': f"${self.stats['total_cost']:.4f}",
            'requests_per_second': self.stats['total_requests'] / max(1, self.stats['total_processing_time'])
        }
    
    def reset_statistics(self):
        """Reset usage statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_extracts': 0,
            'failed_extracts': 0,
            'total_cost': 0.0,
            'total_processing_time': 0.0
        }


# Convenience functions for common use cases
async def extract_article_content(url: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to extract article content from a single URL
    
    Args:
        url: URL to extract content from
        **kwargs: Additional arguments for extraction
        
    Returns:
        Extracted content data
    """
    async with FirecrawlClient() as client:
        return await client.extract_with_retry(url, **kwargs)


async def extract_multiple_articles(urls: List[str], max_concurrent: int = 3, **kwargs) -> List[Dict[str, Any]]:
    """
    Extract content from multiple URLs concurrently
    
    Args:
        urls: List of URLs to extract content from
        max_concurrent: Maximum number of concurrent extractions
        **kwargs: Additional arguments for extraction
        
    Returns:
        List of extracted content data (same order as input URLs)
    """
    async with FirecrawlClient() as client:
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_single(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await client.extract_with_retry(url, **kwargs)
                except Exception as e:
                    return {'url': url, 'error': str(e), 'success': False}
        
        tasks = [extract_single(url) for url in urls]
        return await asyncio.gather(*tasks)