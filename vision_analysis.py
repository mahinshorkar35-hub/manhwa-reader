"""
Vision Analysis Module
Analyzes manga panels using AI vision models.
Supports OpenAI GPT-4 Vision and free alternatives.
"""

import os
import base64
import requests
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass
import openai

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of analyzing a manga panel."""
    description: str
    characters: List[str]
    action: str
    emotion: str
    setting: str
    importance_score: float  # 0.0 to 1.0
    raw_response: str


class BaseVisionProvider:
    """Base class for vision AI providers."""

    def analyze_image(self, image_path: str, prompt: str) -> str:
        raise NotImplementedError

    def analyze_panel(self, image_path: str, context: str = "") -> AnalysisResult:
        raise NotImplementedError

    def analyze_panels_batch(
        self,
        panel_paths: List[str],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[AnalysisResult]:
        raise NotImplementedError


class OpenAIVisionProvider(BaseVisionProvider):
    """OpenAI GPT-4 Vision API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Analyze an image with a custom prompt."""
        try:
            base64_image = self._encode_image(image_path)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI vision analysis failed: {e}")
            raise

    def analyze_panel(self, image_path: str, context: str = "") -> AnalysisResult:
        """Analyze a manga panel with structured output."""
        prompt = f"""Analyze this manga panel and provide a structured description.

Context from previous panels: {context}

Please provide your analysis in this exact format:
DESCRIPTION: [Detailed visual description of what's happening]
CHARACTERS: [Comma-separated list of visible characters]
ACTION: [Main action or event occurring]
EMOTION: [Dominant emotional tone]
SETTING: [Location or scene setting]
IMPORTANCE: [Score from 0.0 to 1.0 indicating how plot-important this panel is]

Be concise but descriptive. Focus on storytelling elements."""

        try:
            response = self.analyze_image(image_path, prompt)
            return self._parse_analysis_response(response, image_path)
        except Exception as e:
            logger.error(f"Panel analysis failed: {e}")
            return self._create_fallback_result(str(e))

    def analyze_panels_batch(
        self,
        panel_paths: List[str],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[AnalysisResult]:
        """Analyze multiple panels with progress tracking."""
        results = []
        total = len(panel_paths)

        for i, panel_path in enumerate(panel_paths):
            try:
                # Build context from previous panels
                context = ""
                if results:
                    last_results = results[-3:]  # Last 3 panels for context
                    context = " | ".join([r.description[:100] for r in last_results])

                result = self.analyze_panel(panel_path, context)
                results.append(result)

                if progress_callback:
                    progress = int((i + 1) / total * 100)
                    progress_callback(f"Analyzing panel {i + 1}/{total}", progress)

            except Exception as e:
                logger.error(f"Failed to analyze panel {panel_path}: {e}")
                results.append(self._create_fallback_result(str(e)))

        return results

    def _parse_analysis_response(self, response: str, image_path: str) -> AnalysisResult:
        """Parse the structured response from the vision model."""
        lines = response.strip().split('\n')
        data = {
            'description': '',
            'characters': [],
            'action': '',
            'emotion': '',
            'setting': '',
            'importance_score': 0.5
        }

        for line in lines:
            line = line.strip()
            if line.startswith('DESCRIPTION:'):
                data['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('CHARACTERS:'):
                chars = line.replace('CHARACTERS:', '').strip()
                data['characters'] = [c.strip() for c in chars.split(',') if c.strip()]
            elif line.startswith('ACTION:'):
                data['action'] = line.replace('ACTION:', '').strip()
            elif line.startswith('EMOTION:'):
                data['emotion'] = line.replace('EMOTION:', '').strip()
            elif line.startswith('SETTING:'):
                data['setting'] = line.replace('SETTING:', '').strip()
            elif line.startswith('IMPORTANCE:'):
                try:
                    score = float(line.replace('IMPORTANCE:', '').strip())
                    data['importance_score'] = max(0.0, min(1.0, score))
                except ValueError:
                    data['importance_score'] = 0.5

        return AnalysisResult(
            description=data['description'],
            characters=data['characters'],
            action=data['action'],
            emotion=data['emotion'],
            setting=data['setting'],
            importance_score=data['importance_score'],
            raw_response=response
        )

    def _create_fallback_result(self, error_msg: str) -> AnalysisResult:
        """Create a fallback result when analysis fails."""
        return AnalysisResult(
            description=f"Analysis failed: {error_msg}",
            characters=[],
            action="Unknown",
            emotion="Unknown",
            setting="Unknown",
            importance_score=0.0,
            raw_response=error_msg
        )


class GeminiVisionProvider(BaseVisionProvider):
    """Google Gemini Pro Vision API provider (free tier available)."""

    def __init__(self, api_key: str, model: str = "gemini-pro-vision"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Analyze an image using Gemini API."""
        try:
            base64_image = self._encode_image(image_path)

            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }]
            }

            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']

        except Exception as e:
            logger.error(f"Gemini vision analysis failed: {e}")
            raise

    def analyze_panel(self, image_path: str, context: str = "") -> AnalysisResult:
        """Analyze a manga panel."""
        prompt = f"""Analyze this manga panel. Context from previous: {context}

Provide:
DESCRIPTION: [What's happening]
CHARACTERS: [Who is present]
ACTION: [Main action]
EMOTION: [Mood/feeling]
SETTING: [Where]
IMPORTANCE: [0.0-1.0 plot importance]"""

        try:
            response = self.analyze_image(image_path, prompt)
            return self._parse_response(response, image_path)
        except Exception as e:
            return self._create_fallback(str(e))

    def analyze_panels_batch(
        self,
        panel_paths: List[str],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[AnalysisResult]:
        """Analyze multiple panels."""
        results = []
        for i, path in enumerate(panel_paths):
            try:
                context = ""
                if results:
                    context = " | ".join([r.description[:100] for r in results[-3:]])
                result = self.analyze_panel(path, context)
                results.append(result)
                if progress_callback:
                    progress_callback(f"Analyzing panel {i+1}/{len(panel_paths)}", int((i+1)/len(panel_paths)*100))
            except Exception as e:
                results.append(self._create_fallback(str(e)))
        return results

    def _parse_response(self, response: str, image_path: str) -> AnalysisResult:
        """Parse Gemini response."""
        # Similar parsing to OpenAI
        lines = response.strip().split('\n')
        data = {'description': '', 'characters': [], 'action': '', 'emotion': '', 'setting': '', 'importance_score': 0.5}
        for line in lines:
            if line.startswith('DESCRIPTION:'): data['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('CHARACTERS:'): data['characters'] = [c.strip() for c in line.split(':', 1)[1].split(',')]
            elif line.startswith('ACTION:'): data['action'] = line.split(':', 1)[1].strip()
            elif line.startswith('EMOTION:'): data['emotion'] = line.split(':', 1)[1].strip()
            elif line.startswith('SETTING:'): data['setting'] = line.split(':', 1)[1].strip()
            elif line.startswith('IMPORTANCE:'):
                try: data['importance_score'] = max(0.0, min(1.0, float(line.split(':', 1)[1].strip())))
                except: pass
        return AnalysisResult(**data, raw_response=response)

    def _create_fallback(self, error: str) -> AnalysisResult:
        return AnalysisResult(description=f"Error: {error}", characters=[], action="", emotion="", setting="", importance_score=0, raw_response=error)


class OllamaVisionProvider(BaseVisionProvider):
    """Ollama local vision model provider (completely free, runs locally).
    Requires Ollama installed with a vision model like 'llava' or 'bakllava'."""

    def __init__(self, model: str = "llava", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def analyze_image(self, image_path: str, prompt: str) -> str:
        try:
            base64_image = self._encode_image(image_path)

            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False
            }

            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get('response', '')

        except requests.exceptions.ConnectionError:
            raise ConnectionError("Ollama not running. Start it with 'ollama serve' or install from ollama.com")
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            raise

    def analyze_panel(self, image_path: str, context: str = "") -> AnalysisResult:
        prompt = f"""Analyze this manga panel. Context: {context}
Format:
DESCRIPTION: [description]
CHARACTERS: [names]
ACTION: [action]
EMOTION: [emotion]
SETTING: [setting]
IMPORTANCE: [0.0-1.0]"""

        try:
            response = self.analyze_image(image_path, prompt)
            return self._parse_response(response, image_path)
        except Exception as e:
            return self._create_fallback(str(e))

    def analyze_panels_batch(
        self,
        panel_paths: List[str],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[AnalysisResult]:
        results = []
        for i, path in enumerate(panel_paths):
            try:
                context = ""
                if results:
                    context = " | ".join([r.description[:100] for r in results[-3:]])
                result = self.analyze_panel(path, context)
                results.append(result)
                if progress_callback:
                    progress_callback(f"Analyzing panel {i+1}/{len(panel_paths)}", int((i+1)/len(panel_paths)*100))
            except Exception as e:
                results.append(self._create_fallback(str(e)))
        return results

    def _parse_response(self, response: str, image_path: str) -> AnalysisResult:
        lines = response.strip().split('\n')
        data = {'description': '', 'characters': [], 'action': '', 'emotion': '', 'setting': '', 'importance_score': 0.5}
        for line in lines:
            if line.startswith('DESCRIPTION:'): data['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('CHARACTERS:'): data['characters'] = [c.strip() for c in line.split(':', 1)[1].split(',')]
            elif line.startswith('ACTION:'): data['action'] = line.split(':', 1)[1].strip()
            elif line.startswith('EMOTION:'): data['emotion'] = line.split(':', 1)[1].strip()
            elif line.startswith('SETTING:'): data['setting'] = line.split(':', 1)[1].strip()
            elif line.startswith('IMPORTANCE:'):
                try: data['importance_score'] = max(0.0, min(1.0, float(line.split(':', 1)[1].strip())))
                except: pass
        return AnalysisResult(**data, raw_response=response)

    def _create_fallback(self, error: str) -> AnalysisResult:
        return AnalysisResult(description=f"Error: {error}", characters=[], action="", emotion="", setting="", importance_score=0, raw_response=error)


class VisionAnalyzer:
    """Main vision analysis orchestrator."""

    PROVIDERS = {
        'openai': OpenAIVisionProvider,
        'gemini': GeminiVisionProvider,
        'ollama': OllamaVisionProvider,
    }

    def __init__(self, provider_name: str = 'openai', **kwargs):
        """
        Initialize the vision analyzer.

        Args:
            provider_name: One of 'openai', 'gemini', 'ollama'
            **kwargs: Provider-specific arguments (api_key, model, etc.)
        """
        provider_class = self.PROVIDERS.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(self.PROVIDERS.keys())}")

        self.provider = provider_class(**kwargs)
        logger.info(f"Initialized vision analyzer with provider: {provider_name}")

    def select_key_panels(
        self,
        panel_analyses: List[AnalysisResult],
        max_panels: int = 20
    ) -> List[Tuple[int, AnalysisResult]]:
        """
        Select the most important panels based on importance scores.

        Args:
            panel_analyses: List of analysis results
            max_panels: Maximum number of panels to select

        Returns:
            List of (index, analysis) tuples sorted by importance
        """
        # Sort by importance score
        indexed = [(i, analysis) for i, analysis in enumerate(panel_analyses)]
        indexed.sort(key=lambda x: x[1].importance_score, reverse=True)

        # Take top panels but maintain original order for narrative flow
        selected = indexed[:max_panels]
        selected.sort(key=lambda x: x[0])  # Sort by original index

        logger.info(f"Selected {len(selected)} key panels from {len(panel_analyses)} total")
        return selected

    def generate_story_summary(
        self,
        panel_analyses: List[AnalysisResult],
        style: str = "dramatic",
        title: str = "",
        volume: str = ""
    ) -> str:
        """
        Generate a cohesive story summary from panel analyses.

        Args:
            panel_analyses: List of panel analysis results
            style: Summary style - "dramatic", "casual", "anime", "concise"
            title: Manga title
            volume: Volume number

        Returns:
            Formatted story summary
        """
        style_instructions = {
            "dramatic": "Write in an epic, dramatic style with vivid descriptions and emotional intensity. Build tension and highlight climactic moments.",
            "casual": "Write in a relaxed, conversational tone as if telling a friend about the story. Keep it accessible and fun.",
            "anime": "Write in an enthusiastic anime-fan style with excitement and references to anime tropes. Use energetic language.",
            "concise": "Write a brief, to-the-point summary focusing only on key plot points and character developments."
        }

        style_instruction = style_instructions.get(style, style_instructions["dramatic"])

        # Build the narrative from panel descriptions
        narrative_parts = []
        for i, analysis in enumerate(panel_analyses):
            if analysis.importance_score > 0.2:  # Only include somewhat important panels
                narrative_parts.append(f"Scene {i+1}: {analysis.description}")

        narrative = "\n".join(narrative_parts)

        # If using OpenAI, we can generate a better summary
        if isinstance(self.provider, OpenAIVisionProvider):
            return self._generate_summary_with_ai(narrative, style_instruction, title, volume)

        # Otherwise, return a formatted summary
        header = f"{title} - Volume {volume}\n\n" if title else ""
        summary = f"{header}{style_instruction}\n\n"
        summary += narrative
        return summary

    def _generate_summary_with_ai(self, narrative: str, style: str, title: str, volume: str) -> str:
        """Use AI to generate a polished summary."""
        try:
            prompt = f"""Create a compelling story summary from these manga scene descriptions.

Manga: {title} Volume {volume}

Style instruction: {style}

Scene descriptions:
{narrative}

Write a cohesive summary that flows naturally between scenes. Include character names, key plot points, emotional beats, and a satisfying narrative arc. Make it engaging and suitable for narration."""

            # Use text-only API for summary generation
            if hasattr(self.provider, 'client'):
                response = self.provider.client.chat.completions.create(
                    model="gpt-4o-mini",  # Use cheaper model for text generation
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"AI summary generation failed, using basic format: {e}")

        return f"{title} - Volume {volume}\n\n{narrative}"
