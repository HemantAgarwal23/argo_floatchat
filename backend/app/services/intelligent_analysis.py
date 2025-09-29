"""
intelligent_analysis.py
MCP-enhanced intelligent analysis services for ARGO FloatChat
"""

from typing import Dict, Any, List, Optional
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import structlog
# Import with error handling to prevent startup issues
try:
    from app.core.database import db_manager
except ImportError:
    db_manager = None

try:
    from app.core.multi_llm_client import multi_llm_client
except ImportError:
    multi_llm_client = None

try:
    from app.services.query_classifier import query_classifier
except ImportError:
    query_classifier = None

logger = structlog.get_logger()


class IntelligentAnalysisService:
    """MCP-enhanced intelligent analysis service for oceanographic data"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.llm_client = multi_llm_client
        self.query_classifier = query_classifier
        self.initialized = all([db_manager, multi_llm_client, query_classifier])
    
    async def analyze_ocean_conditions(self, region: str, parameter: str, 
                                     time_period: str = "", analysis_type: str = "statistical") -> Dict[str, Any]:
        """Perform intelligent oceanographic analysis"""
        try:
            if not self.initialized:
                return {
                    "success": False,
                    "error": "Intelligent analysis service not fully initialized",
                    "region": region,
                    "parameter": parameter
                }
            
            logger.info("Starting intelligent ocean analysis", 
                       region=region, parameter=parameter, analysis_type=analysis_type)
            
            # Build intelligent query
            analysis_query = self._build_analysis_query(region, parameter, time_period, analysis_type)
            
            # Get data using existing RAG pipeline with timeout
            try:
                from app.services.rag_pipeline import rag_pipeline
                result = await asyncio.wait_for(
                    rag_pipeline.process_query(analysis_query, max_results=1000, language="en"),
                    timeout=20.0  # 20 second timeout
                )
            except asyncio.TimeoutError:
                logger.error("RAG pipeline timeout during intelligent analysis")
                return {
                    "success": False,
                    "error": "Analysis timeout - please try a simpler query",
                    "region": region,
                    "parameter": parameter
                }
            
            # Perform intelligent analysis
            analysis_result = await self._perform_intelligent_analysis(
                result.get("retrieved_data", {}), parameter, analysis_type
            )
            
            # Generate contextual insights
            insights = await self._generate_contextual_insights(
                analysis_result, region, parameter, analysis_type
            )
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "region": region,
                "parameter": parameter,
                "time_period": time_period,
                "analysis_result": analysis_result,
                "insights": insights,
                "suggestions": await self._generate_follow_up_suggestions(
                    analysis_result, region, parameter
                ),
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "data_quality": self._assess_data_quality(result.get("retrieved_data", {})),
                    "confidence_score": self._calculate_confidence_score(analysis_result)
                }
            }
            
        except Exception as e:
            logger.error("Error in intelligent ocean analysis", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type,
                "region": region,
                "parameter": parameter
            }
    
    async def detect_anomalies(self, query: str, threshold: float = 2.0) -> Dict[str, Any]:
        """Detect anomalies in oceanographic data"""
        try:
            logger.info("Starting anomaly detection", query=query, threshold=threshold)
            
            # Get data
            from app.services.rag_pipeline import rag_pipeline
            result = await rag_pipeline.process_query(query, max_results=2000, language="en")
            
            # Extract numerical data for analysis
            data = result.get("retrieved_data", {}).get("sql_results", [])
            if not data:
                return {"success": False, "error": "No data found for analysis"}
            
            # Perform statistical anomaly detection
            anomalies = await self._detect_statistical_anomalies(data, threshold)
            
            # Generate anomaly insights
            insights = await self._generate_anomaly_insights(anomalies, query)
            
            return {
                "success": True,
                "query": query,
                "threshold": threshold,
                "anomalies_found": len(anomalies),
                "anomalies": anomalies,
                "insights": insights,
                "recommendations": await self._generate_anomaly_recommendations(anomalies)
            }
            
        except Exception as e:
            logger.error("Error in anomaly detection", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def analyze_trends(self, parameter: str, region: str, time_range: str = "") -> Dict[str, Any]:
        """Analyze trends in oceanographic parameters"""
        try:
            logger.info("Starting trend analysis", parameter=parameter, region=region)
            
            # Build trend analysis query
            trend_query = f"Show {parameter} data in {region}"
            if time_range:
                trend_query += f" for {time_range}"
            
            # Get data
            from app.services.rag_pipeline import rag_pipeline
            result = await rag_pipeline.process_query(trend_query, max_results=1000, language="en")
            
            # Analyze trends
            trends = await self._analyze_temporal_trends(
                result.get("retrieved_data", {}), parameter
            )
            
            # Generate trend insights
            insights = await self._generate_trend_insights(trends, parameter, region)
            
            return {
                "success": True,
                "parameter": parameter,
                "region": region,
                "time_range": time_range,
                "trends": trends,
                "insights": insights,
                "predictions": await self._generate_trend_predictions(trends),
                "significance": self._assess_trend_significance(trends)
            }
            
        except Exception as e:
            logger.error("Error in trend analysis", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def find_correlations(self, parameters: List[str], region: str = "") -> Dict[str, Any]:
        """Find correlations between oceanographic parameters"""
        try:
            logger.info("Starting correlation analysis", parameters=parameters, region=region)
            
            # Build correlation query
            param_list = ", ".join(parameters)
            correlation_query = f"Show {param_list} data"
            if region:
                correlation_query += f" in {region}"
            
            # Get data
            from app.services.rag_pipeline import rag_pipeline
            result = await rag_pipeline.process_query(correlation_query, max_results=2000, language="en")
            
            # Calculate correlations
            correlations = await self._calculate_parameter_correlations(
                result.get("retrieved_data", {}), parameters
            )
            
            # Generate correlation insights
            insights = await self._generate_correlation_insights(correlations, parameters)
            
            return {
                "success": True,
                "parameters": parameters,
                "region": region,
                "correlations": correlations,
                "insights": insights,
                "strength_assessment": self._assess_correlation_strength(correlations),
                "oceanographic_significance": await self._assess_oceanographic_significance(correlations)
            }
            
        except Exception as e:
            logger.error("Error in correlation analysis", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def generate_smart_suggestions(self, current_query: str, user_history: List[str] = None) -> Dict[str, Any]:
        """Generate intelligent suggestions based on current query and user behavior"""
        try:
            logger.info("Generating smart suggestions", query=current_query)
            
            # Analyze current query
            query_analysis = self.query_classifier.classify_query(current_query)
            
            # Get related data to understand context
            from app.services.rag_pipeline import rag_pipeline
            result = await rag_pipeline.process_query(current_query, max_results=100, language="en")
            
            # Generate contextual suggestions
            suggestions = await self._generate_contextual_suggestions(
                current_query, query_analysis, result.get("retrieved_data", {})
            )
            
            # Generate follow-up questions
            follow_ups = await self._generate_follow_up_questions(
                current_query, query_analysis, result.get("retrieved_data", {})
            )
            
            # Generate related analyses
            related_analyses = await self._generate_related_analyses(
                current_query, query_analysis, result.get("retrieved_data", {})
            )
            
            return {
                "success": True,
                "current_query": current_query,
                "query_analysis": query_analysis,
                "suggestions": suggestions,
                "follow_up_questions": follow_ups,
                "related_analyses": related_analyses,
                "smart_recommendations": await self._generate_smart_recommendations(
                    current_query, suggestions, follow_ups
                )
            }
            
        except Exception as e:
            logger.error("Error generating smart suggestions", error=str(e))
            return {"success": False, "error": str(e)}
    
    # Helper methods
    def _build_analysis_query(self, region: str, parameter: str, time_period: str, analysis_type: str) -> str:
        """Build intelligent analysis query"""
        query_parts = []
        
        if analysis_type == "trend":
            query_parts.append(f"Show trends in {parameter} data")
        elif analysis_type == "anomaly":
            query_parts.append(f"Find anomalies in {parameter} data")
        elif analysis_type == "comparison":
            query_parts.append(f"Compare {parameter} data")
        elif analysis_type == "correlation":
            query_parts.append(f"Find correlations in {parameter} data")
        else:
            query_parts.append(f"Analyze {parameter} data")
        
        if region:
            query_parts.append(f"in {region}")
        if time_period:
            query_parts.append(f"during {time_period}")
        
        return " ".join(query_parts)
    
    async def _perform_intelligent_analysis(self, data: Dict[str, Any], parameter: str, analysis_type: str) -> Dict[str, Any]:
        """Perform intelligent analysis on the data"""
        try:
            sql_results = data.get("sql_results", [])
            if not sql_results:
                return {"error": "No data available for analysis"}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(sql_results)
            
            analysis_result = {
                "total_records": len(df),
                "parameter": parameter,
                "analysis_type": analysis_type
            }
            
            # Statistical analysis
            if parameter in df.columns:
                analysis_result["statistics"] = {
                    "mean": float(df[parameter].mean()) if pd.notna(df[parameter].mean()) else None,
                    "std": float(df[parameter].std()) if pd.notna(df[parameter].std()) else None,
                    "min": float(df[parameter].min()) if pd.notna(df[parameter].min()) else None,
                    "max": float(df[parameter].max()) if pd.notna(df[parameter].max()) else None,
                    "median": float(df[parameter].median()) if pd.notna(df[parameter].median()) else None
                }
            
            # Geographic analysis
            if "latitude" in df.columns and "longitude" in df.columns:
                analysis_result["geographic_analysis"] = {
                    "lat_range": [float(df["latitude"].min()), float(df["latitude"].max())],
                    "lon_range": [float(df["longitude"].min()), float(df["longitude"].max())],
                    "center_lat": float(df["latitude"].mean()),
                    "center_lon": float(df["longitude"].mean())
                }
            
            # Temporal analysis
            if "profile_date" in df.columns:
                df["profile_date"] = pd.to_datetime(df["profile_date"], errors='coerce')
                date_range = df["profile_date"].dropna()
                if not date_range.empty:
                    analysis_result["temporal_analysis"] = {
                        "date_range": [date_range.min().isoformat(), date_range.max().isoformat()],
                        "total_days": (date_range.max() - date_range.min()).days,
                        "records_per_month": len(date_range) / max(1, (date_range.max() - date_range.min()).days / 30)
                    }
            
            return analysis_result
            
        except Exception as e:
            logger.error("Error in intelligent analysis", error=str(e))
            return {"error": str(e)}
    
    async def _generate_contextual_insights(self, analysis_result: Dict[str, Any], 
                                          region: str, parameter: str, analysis_type: str) -> List[str]:
        """Generate contextual insights using LLM"""
        try:
            insights_prompt = f"""
            Based on this oceanographic analysis, provide 3-5 key insights:
            
            Analysis Results: {analysis_result}
            Region: {region}
            Parameter: {parameter}
            Analysis Type: {analysis_type}
            
            Provide scientific, oceanographic insights that would be valuable to researchers.
            Focus on patterns, anomalies, and scientific significance.
            """
            
            insights_text = await self.llm_client.generate_text(
                insights_prompt, max_tokens=500, temperature=0.7
            )
            
            # Split into individual insights
            insights = [insight.strip() for insight in insights_text.split('\n') if insight.strip()]
            return insights[:5]  # Limit to 5 insights
            
        except Exception as e:
            logger.error("Error generating contextual insights", error=str(e))
            return [f"Analysis completed for {parameter} in {region}"]
    
    async def _generate_follow_up_suggestions(self, analysis_result: Dict[str, Any], 
                                            region: str, parameter: str) -> List[str]:
        """Generate intelligent follow-up suggestions"""
        try:
            suggestions_prompt = f"""
            Based on this oceanographic analysis, suggest 3-4 follow-up queries:
            
            Analysis: {analysis_result}
            Region: {region}
            Parameter: {parameter}
            
            Suggest specific, actionable queries that would provide deeper insights.
            """
            
            suggestions_text = await self.llm_client.generate_text(
                suggestions_prompt, max_tokens=300, temperature=0.8
            )
            
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
            return suggestions[:4]
            
        except Exception as e:
            logger.error("Error generating follow-up suggestions", error=str(e))
            return [
                f"Compare {parameter} with other parameters in {region}",
                f"Analyze {parameter} trends over time in {region}",
                f"Find correlations between {parameter} and environmental factors"
            ]
    
    async def _detect_statistical_anomalies(self, data: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
        """Detect statistical anomalies in the data"""
        try:
            df = pd.DataFrame(data)
            anomalies = []
            
            # Look for numerical columns
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numerical_cols:
                if col in ['latitude', 'longitude', 'profile_id']:
                    continue  # Skip non-parameter columns
                
                values = df[col].dropna()
                if len(values) < 10:  # Need sufficient data
                    continue
                
                mean_val = values.mean()
                std_val = values.std()
                
                if std_val == 0:  # No variation
                    continue
                
                # Find outliers (beyond threshold standard deviations)
                outliers = values[abs(values - mean_val) > threshold * std_val]
                
                for idx, value in outliers.items():
                    anomalies.append({
                        "parameter": col,
                        "value": float(value),
                        "mean": float(mean_val),
                        "std": float(std_val),
                        "z_score": float((value - mean_val) / std_val),
                        "record_index": int(idx),
                        "severity": "high" if abs((value - mean_val) / std_val) > 3 else "medium"
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error("Error detecting anomalies", error=str(e))
            return []
    
    async def _generate_anomaly_insights(self, anomalies: List[Dict[str, Any]], query: str) -> List[str]:
        """Generate insights about detected anomalies"""
        try:
            if not anomalies:
                return ["No significant anomalies detected in the data"]
            
            insights = []
            
            # Group by parameter
            param_groups = {}
            for anomaly in anomalies:
                param = anomaly["parameter"]
                if param not in param_groups:
                    param_groups[param] = []
                param_groups[param].append(anomaly)
            
            for param, param_anomalies in param_groups.items():
                count = len(param_anomalies)
                high_severity = len([a for a in param_anomalies if a["severity"] == "high"])
                
                insights.append(f"Found {count} anomalies in {param} ({high_severity} high severity)")
                
                # Most extreme anomaly
                most_extreme = max(param_anomalies, key=lambda x: abs(x["z_score"]))
                insights.append(f"Most extreme {param} anomaly: {most_extreme['value']} (z-score: {most_extreme['z_score']:.2f})")
            
            return insights
            
        except Exception as e:
            logger.error("Error generating anomaly insights", error=str(e))
            return ["Anomaly analysis completed"]
    
    async def _generate_anomaly_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on anomalies"""
        recommendations = []
        
        if not anomalies:
            recommendations.append("Data appears to be within normal ranges")
            return recommendations
        
        high_severity_count = len([a for a in anomalies if a["severity"] == "high"])
        
        if high_severity_count > 0:
            recommendations.append(f"Investigate {high_severity_count} high-severity anomalies further")
            recommendations.append("Consider data quality checks for extreme values")
        
        recommendations.append("Compare anomalous periods with environmental conditions")
        recommendations.append("Analyze temporal patterns in anomaly occurrences")
        
        return recommendations
    
    async def _analyze_temporal_trends(self, data: Dict[str, Any], parameter: str) -> Dict[str, Any]:
        """Analyze temporal trends in the data"""
        try:
            sql_results = data.get("sql_results", [])
            if not sql_results:
                return {"error": "No data available"}
            
            df = pd.DataFrame(sql_results)
            
            if "profile_date" not in df.columns or parameter not in df.columns:
                return {"error": "Required columns not found"}
            
            df["profile_date"] = pd.to_datetime(df["profile_date"], errors='coerce')
            df = df.dropna(subset=["profile_date", parameter])
            
            if len(df) < 10:
                return {"error": "Insufficient data for trend analysis"}
            
            # Sort by date
            df = df.sort_values("profile_date")
            
            # Calculate monthly averages
            df["year_month"] = df["profile_date"].dt.to_period('M')
            monthly_avg = df.groupby("year_month")[parameter].mean()
            
            # Calculate trend
            x = np.arange(len(monthly_avg))
            y = monthly_avg.values
            slope, intercept = np.polyfit(x, y, 1)
            
            # Calculate trend strength
            correlation = np.corrcoef(x, y)[0, 1]
            
            return {
                "trend_direction": "increasing" if slope > 0 else "decreasing",
                "trend_slope": float(slope),
                "trend_strength": abs(float(correlation)),
                "monthly_averages": monthly_avg.to_dict(),
                "data_points": len(df),
                "date_range": [df["profile_date"].min().isoformat(), df["profile_date"].max().isoformat()]
            }
            
        except Exception as e:
            logger.error("Error analyzing trends", error=str(e))
            return {"error": str(e)}
    
    async def _generate_trend_insights(self, trends: Dict[str, Any], parameter: str, region: str) -> List[str]:
        """Generate insights about trends"""
        try:
            if "error" in trends:
                return [f"Trend analysis not available: {trends['error']}"]
            
            insights = []
            
            direction = trends["trend_direction"]
            strength = trends["trend_strength"]
            
            insights.append(f"{parameter} in {region} shows a {direction} trend")
            
            if strength > 0.7:
                insights.append("This is a strong, statistically significant trend")
            elif strength > 0.5:
                insights.append("This is a moderate trend worth monitoring")
            else:
                insights.append("This is a weak trend that may not be significant")
            
            insights.append(f"Trend analysis based on {trends['data_points']} data points")
            
            return insights
            
        except Exception as e:
            logger.error("Error generating trend insights", error=str(e))
            return ["Trend analysis completed"]
    
    async def _generate_trend_predictions(self, trends: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions based on trends"""
        try:
            if "error" in trends:
                return {"error": trends["error"]}
            
            slope = trends["trend_slope"]
            monthly_data = trends["monthly_averages"]
            
            # Simple linear prediction for next 6 months
            last_month = max(monthly_data.keys())
            predictions = {}
            
            for i in range(1, 7):
                next_month = last_month + i
                predicted_value = list(monthly_data.values())[-1] + slope * i
                predictions[str(next_month)] = float(predicted_value)
            
            return {
                "predictions": predictions,
                "confidence": "low" if trends["trend_strength"] < 0.5 else "medium",
                "note": "Predictions based on linear trend assumption"
            }
            
        except Exception as e:
            logger.error("Error generating predictions", error=str(e))
            return {"error": str(e)}
    
    def _assess_trend_significance(self, trends: Dict[str, Any]) -> str:
        """Assess the significance of trends"""
        try:
            if "error" in trends:
                return "insignificant"
            
            strength = trends["trend_strength"]
            
            if strength > 0.8:
                return "highly_significant"
            elif strength > 0.6:
                return "significant"
            elif strength > 0.4:
                return "moderate"
            else:
                return "weak"
                
        except Exception as e:
            logger.error("Error assessing trend significance", error=str(e))
            return "unknown"
    
    async def _calculate_parameter_correlations(self, data: Dict[str, Any], parameters: List[str]) -> Dict[str, Any]:
        """Calculate correlations between parameters"""
        try:
            sql_results = data.get("sql_results", [])
            if not sql_results:
                return {"error": "No data available"}
            
            df = pd.DataFrame(sql_results)
            
            # Check which parameters are available
            available_params = [p for p in parameters if p in df.columns]
            if len(available_params) < 2:
                return {"error": f"Insufficient parameters available. Found: {available_params}"}
            
            # Calculate correlation matrix
            correlation_matrix = df[available_params].corr()
            
            # Find strongest correlations
            correlations = []
            for i in range(len(available_params)):
                for j in range(i+1, len(available_params)):
                    param1, param2 = available_params[i], available_params[j]
                    corr_value = correlation_matrix.loc[param1, param2]
                    
                    if not pd.isna(corr_value):
                        correlations.append({
                            "parameter1": param1,
                            "parameter2": param2,
                            "correlation": float(corr_value),
                            "strength": self._classify_correlation_strength(abs(corr_value))
                        })
            
            # Sort by absolute correlation value
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            return {
                "correlation_matrix": correlation_matrix.to_dict(),
                "strongest_correlations": correlations[:5],
                "parameters_analyzed": available_params,
                "data_points": len(df)
            }
            
        except Exception as e:
            logger.error("Error calculating correlations", error=str(e))
            return {"error": str(e)}
    
    def _classify_correlation_strength(self, abs_corr: float) -> str:
        """Classify correlation strength"""
        if abs_corr > 0.8:
            return "very_strong"
        elif abs_corr > 0.6:
            return "strong"
        elif abs_corr > 0.4:
            return "moderate"
        elif abs_corr > 0.2:
            return "weak"
        else:
            return "very_weak"
    
    async def _generate_correlation_insights(self, correlations: Dict[str, Any], parameters: List[str]) -> List[str]:
        """Generate insights about correlations"""
        try:
            if "error" in correlations:
                return [f"Correlation analysis not available: {correlations['error']}"]
            
            insights = []
            
            strongest = correlations["strongest_correlations"]
            if not strongest:
                insights.append("No significant correlations found between the parameters")
                return insights
            
            top_correlation = strongest[0]
            insights.append(f"Strongest correlation: {top_correlation['parameter1']} and {top_correlation['parameter2']} ({top_correlation['strength']})")
            
            # Oceanographic interpretation
            if "temperature" in top_correlation["parameter1"].lower() and "salinity" in top_correlation["parameter2"].lower():
                insights.append("Temperature-salinity correlation is fundamental to ocean circulation")
            elif "chlorophyll" in top_correlation["parameter1"].lower() and "nitrate" in top_correlation["parameter2"].lower():
                insights.append("Chlorophyll-nitrate correlation indicates biological productivity patterns")
            
            insights.append(f"Analysis based on {correlations['data_points']} data points")
            
            return insights
            
        except Exception as e:
            logger.error("Error generating correlation insights", error=str(e))
            return ["Correlation analysis completed"]
    
    def _assess_correlation_strength(self, correlations: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall correlation strength"""
        try:
            if "error" in correlations:
                return {"assessment": "failed", "reason": correlations["error"]}
            
            strongest = correlations["strongest_correlations"]
            if not strongest:
                return {"assessment": "no_correlations", "strength": "none"}
            
            # Count correlation strengths
            strength_counts = {}
            for corr in strongest:
                strength = corr["strength"]
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
            
            return {
                "assessment": "completed",
                "strength_distribution": strength_counts,
                "overall_strength": strongest[0]["strength"] if strongest else "none"
            }
            
        except Exception as e:
            logger.error("Error assessing correlation strength", error=str(e))
            return {"assessment": "error", "error": str(e)}
    
    async def _assess_oceanographic_significance(self, correlations: Dict[str, Any]) -> List[str]:
        """Assess oceanographic significance of correlations"""
        try:
            if "error" in correlations:
                return [f"Cannot assess significance: {correlations['error']}"]
            
            insights = []
            strongest = correlations["strongest_correlations"]
            
            for corr in strongest[:3]:  # Top 3 correlations
                param1, param2 = corr["parameter1"], corr["parameter2"]
                strength = corr["strength"]
                
                if strength in ["very_strong", "strong"]:
                    insights.append(f"Strong {param1}-{param2} correlation has oceanographic significance")
                    
                    # Specific oceanographic interpretations
                    if "temperature" in param1.lower() and "salinity" in param2.lower():
                        insights.append("T-S relationship indicates water mass characteristics")
                    elif "chlorophyll" in param1.lower() and any(p in param2.lower() for p in ["nitrate", "phosphate"]):
                        insights.append("Nutrient-chlorophyll correlation shows biological productivity")
            
            return insights
            
        except Exception as e:
            logger.error("Error assessing oceanographic significance", error=str(e))
            return ["Oceanographic significance assessment completed"]
    
    async def _generate_contextual_suggestions(self, query: str, query_analysis: Dict[str, Any], 
                                             data: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestions based on current query"""
        try:
            suggestions_prompt = f"""
            Based on this oceanographic query and analysis, suggest 3-4 related queries:
            
            Current Query: {query}
            Query Analysis: {query_analysis}
            Data Available: {len(data.get('sql_results', []))} records
            
            Suggest specific, actionable oceanographic queries that would complement this analysis.
            Focus on scientific insights and data exploration.
            """
            
            suggestions_text = await self.llm_client.generate_text(
                suggestions_prompt, max_tokens=400, temperature=0.8
            )
            
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
            return suggestions[:4]
            
        except Exception as e:
            logger.error("Error generating contextual suggestions", error=str(e))
            return [
                "Analyze temporal trends in this data",
                "Compare with other ocean regions",
                "Investigate correlations with environmental factors",
                "Look for seasonal patterns"
            ]
    
    async def _generate_follow_up_questions(self, query: str, query_analysis: Dict[str, Any], 
                                          data: Dict[str, Any]) -> List[str]:
        """Generate intelligent follow-up questions"""
        try:
            follow_up_prompt = f"""
            Based on this oceanographic query, generate 3-4 natural follow-up questions:
            
            Query: {query}
            Analysis Type: {query_analysis.get('query_type', 'unknown')}
            
            Generate questions that a researcher might naturally ask next.
            """
            
            follow_up_text = await self.llm_client.generate_text(
                follow_up_prompt, max_tokens=300, temperature=0.9
            )
            
            questions = [q.strip() for q in follow_up_text.split('\n') if q.strip()]
            return questions[:4]
            
        except Exception as e:
            logger.error("Error generating follow-up questions", error=str(e))
            return [
                "What causes these patterns?",
                "How do these compare to other regions?",
                "What are the seasonal variations?",
                "Are there any anomalies in this data?"
            ]
    
    async def _generate_related_analyses(self, query: str, query_analysis: Dict[str, Any], 
                                       data: Dict[str, Any]) -> List[str]:
        """Generate related analysis suggestions"""
        try:
            analyses = []
            
            query_type = query_analysis.get("query_type", "")
            
            if "temperature" in query.lower():
                analyses.extend([
                    "Analyze temperature-depth profiles",
                    "Compare surface vs deep temperature trends",
                    "Investigate temperature-salinity relationships"
                ])
            elif "salinity" in query.lower():
                analyses.extend([
                    "Analyze salinity distribution patterns",
                    "Compare salinity with temperature",
                    "Investigate freshwater influence on salinity"
                ])
            elif "trajectory" in query.lower() or "float" in query.lower():
                analyses.extend([
                    "Analyze float drift patterns",
                    "Compare trajectory speeds",
                    "Investigate seasonal movement patterns"
                ])
            
            return analyses[:3]
            
        except Exception as e:
            logger.error("Error generating related analyses", error=str(e))
            return [
                "Perform statistical analysis",
                "Generate temporal trends",
                "Compare with other datasets"
            ]
    
    async def _generate_smart_recommendations(self, query: str, suggestions: List[str], 
                                            follow_ups: List[str]) -> List[str]:
        """Generate smart recommendations combining all suggestions"""
        try:
            recommendations = []
            
            # Combine and prioritize suggestions
            all_suggestions = suggestions + follow_ups
            
            # Remove duplicates and select best ones
            unique_suggestions = list(dict.fromkeys(all_suggestions))
            
            recommendations.extend(unique_suggestions[:4])
            
            return recommendations
            
        except Exception as e:
            logger.error("Error generating smart recommendations", error=str(e))
            return suggestions[:4]
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the data"""
        try:
            sql_results = data.get("sql_results", [])
            if not sql_results:
                return {"quality": "no_data", "score": 0}
            
            df = pd.DataFrame(sql_results)
            
            # Calculate quality metrics
            total_records = len(df)
            null_percentage = (df.isnull().sum().sum() / (total_records * len(df.columns))) * 100
            
            # Assess quality
            if null_percentage < 5:
                quality = "excellent"
                score = 95
            elif null_percentage < 15:
                quality = "good"
                score = 80
            elif null_percentage < 30:
                quality = "fair"
                score = 60
            else:
                quality = "poor"
                score = 40
            
            return {
                "quality": quality,
                "score": score,
                "total_records": total_records,
                "null_percentage": round(null_percentage, 2),
                "columns": len(df.columns)
            }
            
        except Exception as e:
            logger.error("Error assessing data quality", error=str(e))
            return {"quality": "unknown", "score": 0, "error": str(e)}
    
    def _calculate_confidence_score(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis"""
        try:
            score = 50.0  # Base score
            
            # Increase score based on data quality
            if "total_records" in analysis_result:
                records = analysis_result["total_records"]
                if records > 1000:
                    score += 20
                elif records > 100:
                    score += 10
                elif records > 10:
                    score += 5
            
            # Increase score based on analysis completeness
            if "statistics" in analysis_result:
                score += 15
            if "geographic_analysis" in analysis_result:
                score += 10
            if "temporal_analysis" in analysis_result:
                score += 10
            
            return min(100.0, score)
            
        except Exception as e:
            logger.error("Error calculating confidence score", error=str(e))
            return 50.0


# Create global instance
intelligent_analysis_service = IntelligentAnalysisService()
