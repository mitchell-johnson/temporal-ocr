#!/usr/bin/env python3
# AIDEV-NOTE: Test script for AI temporal workflows
"""
Test script to demonstrate running the three AI workflow examples.
This script starts workflows and displays their results.
"""

import asyncio
import os
import json
from temporalio.client import Client
from datetime import datetime

# Add the app directory to the Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.ai_models import MultiAIWorkflowInput
from app.workflows.ai_example_workflows import (
    AIConsensusWorkflow,
    AIChainWorkflow,
    AISpecialistWorkflow
)

TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')

async def test_consensus_workflow(client: Client):
    """Test the consensus workflow with all three AI providers"""
    print("\n" + "="*60)
    print("Testing AI Consensus Workflow")
    print("="*60)
    
    # Prepare input
    workflow_input = MultiAIWorkflowInput(
        initial_prompt="What are the key considerations when building a microservices architecture?",
        providers=["gemini", "openai", "anthropic"]
    )
    
    # Start workflow
    handle = await client.start_workflow(
        AIConsensusWorkflow.run,
        workflow_input,
        id=f"consensus-workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        task_queue="ai-workflow-queue"
    )
    
    print(f"Started workflow: {handle.id}")
    
    # Wait for result
    result = await handle.result()
    
    print("\nWorkflow completed!")
    print(f"Analysis: {result.analysis}")
    print("\nIndividual responses:")
    for provider, response in result.results.items():
        print(f"\n{provider.upper()}:")
        print(f"- Model: {response.model_used}")
        print(f"- Response preview: {response.content[:200]}...")
    
    print(f"\nConsensus:\n{result.consensus[:500]}...")
    
    return result

async def test_chain_workflow(client: Client):
    """Test the chain workflow where each AI builds on the previous"""
    print("\n" + "="*60)
    print("Testing AI Chain Workflow")
    print("="*60)
    
    # Prepare input with a sample file
    workflow_input = MultiAIWorkflowInput(
        initial_prompt="Analyze the architectural patterns and provide recommendations",
        file_path="docs/fishinglicence.png" if os.path.exists("docs/fishinglicence.png") else None
    )
    
    # Start workflow
    handle = await client.start_workflow(
        AIChainWorkflow.run,
        workflow_input,
        id=f"chain-workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        task_queue="ai-workflow-queue"
    )
    
    print(f"Started workflow: {handle.id}")
    
    # Wait for result
    result = await handle.result()
    
    print("\nWorkflow completed!")
    print(f"Analysis: {result.analysis}")
    print("\nProcessing chain:")
    print(f"1. Gemini (initial): {result.results['gemini'].content[:200]}...")
    print(f"2. OpenAI (refined): {result.results['openai'].content[:200]}...")
    print(f"3. Anthropic (final): {result.results['anthropic'].content[:200]}...")
    
    return result

async def test_specialist_workflow(client: Client):
    """Test the specialist workflow using each AI for its strengths"""
    print("\n" + "="*60)
    print("Testing AI Specialist Workflow")
    print("="*60)
    
    # Prepare input
    workflow_input = MultiAIWorkflowInput(
        initial_prompt="Design a real-time data processing system for IoT devices",
        providers=["gemini", "openai", "anthropic"]
    )
    
    # Start workflow
    handle = await client.start_workflow(
        AISpecialistWorkflow.run,
        workflow_input,
        id=f"specialist-workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        task_queue="ai-workflow-queue"
    )
    
    print(f"Started workflow: {handle.id}")
    
    # Wait for result
    result = await handle.result()
    
    print("\nWorkflow completed!")
    print(f"Analysis: {result.analysis}")
    print("\nSpecialized analyses:")
    print(f"- Gemini (creative/visual): {result.results['gemini'].content[:200]}...")
    print(f"- OpenAI (technical): {result.results['openai'].content[:200]}...")
    print(f"- Anthropic (analytical): {result.results['anthropic'].content[:200]}...")
    print(f"\nSynthesized result:\n{result.consensus[:500]}...")
    
    return result

async def main():
    """Main test function"""
    print("Connecting to Temporal...")
    client = await Client.connect(TEMPORAL_HOST)
    print(f"Connected to Temporal at: {TEMPORAL_HOST}")
    
    try:
        # Test all three workflows
        consensus_result = await test_consensus_workflow(client)
        chain_result = await test_chain_workflow(client)
        specialist_result = await test_specialist_workflow(client)
        
        # Save results
        results = {
            "consensus_workflow": {
                "analysis": consensus_result.analysis,
                "consensus": consensus_result.consensus,
                "provider_count": len(consensus_result.results)
            },
            "chain_workflow": {
                "analysis": chain_result.analysis,
                "final_result": chain_result.consensus[:1000]
            },
            "specialist_workflow": {
                "analysis": specialist_result.analysis,
                "synthesis": specialist_result.consensus[:1000]
            }
        }
        
        with open("ai_workflow_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("Results saved to: ai_workflow_test_results.json")
        print("="*60)
        
    except Exception as e:
        print(f"\nError running workflows: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())