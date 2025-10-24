"""
Abstract Geometric Art Data Processor
Converts literacy rate data into geometric shapes and mathematical parameters
"""

import pandas as pd
import numpy as np
import json
import math

class GeometricDataProcessor:
    def __init__(self):
        self.shapes = ['circle', 'triangle', 'square', 'hexagon', 'pentagon']
        self.patterns = ['solid', 'outline', 'dotted', 'gradient', 'striped']
        
    def process_literacy_data(self):
        """Process literacy rate data and convert to geometric parameters"""
        try:
            # Read CSV data
            df = pd.read_csv('cross-country-literacy-rates.csv')
            print(f"Original data: {df.shape[0]} records")
            
            # Data cleaning
            df_clean = df.dropna(subset=['Literacy rate'])
            df_clean = df_clean[(df_clean['Literacy rate'] >= 0) & (df_clean['Literacy rate'] <= 100)]
            
            # Get latest data for each country/region
            latest_data = df_clean.sort_values('Year').groupby('Entity').tail(1).reset_index(drop=True)
            
            # Reduce entity count - select representative countries
            # Stratified sampling to ensure all literacy levels are represented
            sampled_data = self.sample_representative_entities(latest_data)
            print(f"Processed data: {len(sampled_data)} entities (selected from {len(latest_data)})")
            
            # Convert to geometric parameters
            geometric_data = []
            for _, row in sampled_data.iterrows():
                entity_data = self.create_geometric_entity(row)
                geometric_data.append(entity_data)
            
            # Save geometric data
            with open('geometric_data.json', 'w', encoding='utf-8') as f:
                json.dump(geometric_data, f, ensure_ascii=False, indent=2)
            
            # Generate statistics
            stats = self.generate_statistics(geometric_data)
            with open('geometric_stats.json', 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            print("✅ Geometric data processing completed")
            return geometric_data, stats
            
        except Exception as e:
            print(f"❌ Data processing error: {e}")
            return [], {}
    
    def sample_representative_entities(self, data):
        """Sample representative entities to reduce count while maintaining data diversity"""
        # Stratify by literacy rate
        high_literacy = data[data['Literacy rate'] >= 90]      # High literacy
        medium_high = data[(data['Literacy rate'] >= 70) & (data['Literacy rate'] < 90)]  # Medium-high
        medium = data[(data['Literacy rate'] >= 50) & (data['Literacy rate'] < 70)]       # Medium
        low = data[data['Literacy rate'] < 50]                 # Low literacy
        
        # Sample size per tier
        samples_per_tier = {
            'high': min(15, len(high_literacy)),      # High literacy: 15 entities
            'medium_high': min(12, len(medium_high)), # Medium-high: 12 entities
            'medium': min(10, len(medium)),           # Medium: 10 entities
            'low': min(8, len(low))                   # Low: 8 entities
        }
        
        sampled_entities = []
        
        # High literacy sampling (including well-known developed countries)
        if len(high_literacy) > 0:
            # Prioritize well-known countries
            priority_countries = ['Finland', 'Norway', 'Denmark', 'Germany', 'Japan', 'United States', 
                                'Canada', 'Australia', 'United Kingdom', 'France', 'Sweden']
            priority_sample = high_literacy[high_literacy['Entity'].isin(priority_countries)]
            remaining_high = high_literacy[~high_literacy['Entity'].isin(priority_countries)]
            
            # Combine priority countries and random sampling
            if len(priority_sample) > 0:
                sampled_entities.append(priority_sample.head(min(10, samples_per_tier['high'])))
                remaining_count = samples_per_tier['high'] - len(priority_sample.head(10))
                if remaining_count > 0 and len(remaining_high) > 0:
                    sampled_entities.append(remaining_high.sample(min(remaining_count, len(remaining_high))))
            else:
                sampled_entities.append(high_literacy.sample(samples_per_tier['high']))
        
        # Medium-high literacy sampling
        if len(medium_high) > 0:
            sampled_entities.append(medium_high.sample(samples_per_tier['medium_high']))
        
        # Medium literacy sampling
        if len(medium) > 0:
            sampled_entities.append(medium.sample(samples_per_tier['medium']))
        
        # Low literacy sampling
        if len(low) > 0:
            sampled_entities.append(low.sample(samples_per_tier['low']))
        
        # Combine all sampling results
        if sampled_entities:
            result = pd.concat(sampled_entities, ignore_index=True)
            print(f"📊 Sampling distribution: High literacy({samples_per_tier['high']}) + "
                  f"Medium-high({samples_per_tier['medium_high']}) + "
                  f"Medium({samples_per_tier['medium']}) + "
                  f"Low({samples_per_tier['low']}) = {len(result)} entities")
            return result
        else:
            return data.head(50)  # Fallback option
    
    def create_geometric_entity(self, row):
        """Create geometric parameters for each entity"""
        literacy_rate = float(row['Literacy rate'])
        
        # Basic geometric parameters
        shape = self.get_shape_by_literacy(literacy_rate)
        size = self.calculate_size(literacy_rate)
        pattern = self.get_pattern_by_literacy(literacy_rate)
        
        # Position parameters (normalized to 0-1 range)
        x = np.random.uniform(0, 1)
        y = np.random.uniform(0, 1)
        
        # Motion parameters
        velocity = self.calculate_velocity(literacy_rate)
        angular_velocity = self.calculate_angular_velocity(literacy_rate)
        
        # Color parameters (HSL color space) - pentagons use warm tones
        hue = self.map_literacy_to_hue_with_shape(literacy_rate, shape)
        saturation = self.calculate_saturation(literacy_rate)
        lightness = self.calculate_lightness(literacy_rate)
        
        # Geometric transformation parameters
        rotation = np.random.uniform(0, 360)
        scale_factor = self.calculate_scale_factor(literacy_rate)
        
        # Animation parameters
        oscillation_amplitude = self.calculate_oscillation(literacy_rate)
        frequency = self.calculate_frequency(literacy_rate)
        phase = np.random.uniform(0, 2 * math.pi)
        
        return {
            'entity': row['Entity'],
            'code': row['Code'] if pd.notna(row['Code']) else '',
            'year': int(row['Year']),
            'literacy_rate': literacy_rate,
            
            # Geometric properties
            'shape': shape,
            'size': size,
            'pattern': pattern,
            
            # Position and motion
            'x': x,
            'y': y,
            'velocity': velocity,
            'angular_velocity': angular_velocity,
            
            # Visual properties
            'hue': hue,
            'saturation': saturation,
            'lightness': lightness,
            'opacity': self.calculate_opacity(literacy_rate),
            
            # Transformation parameters
            'rotation': rotation,
            'scale_factor': scale_factor,
            
            # Animation parameters
            'oscillation_amplitude': oscillation_amplitude,
            'frequency': frequency,
            'phase': phase,
            
            # Mathematical parameters
            'complexity_level': self.calculate_complexity(literacy_rate),
            'symmetry_order': self.calculate_symmetry(literacy_rate),
            'edge_count': self.get_edge_count(shape)
        }
    
    def get_shape_by_literacy(self, literacy_rate):
        """Determine geometric shape based on literacy rate"""
        if literacy_rate >= 90:
            return 'hexagon'      # Most complex shape
        elif literacy_rate >= 75:
            return 'pentagon'     # High complexity
        elif literacy_rate >= 60:
            return 'square'       # Medium complexity
        elif literacy_rate >= 40:
            return 'triangle'     # Basic shape
        else:
            return 'circle'       # Simplest shape
    
    def get_pattern_by_literacy(self, literacy_rate):
        """Determine pattern type based on literacy rate"""
        if literacy_rate >= 85:
            return 'gradient'
        elif literacy_rate >= 70:
            return 'striped'
        elif literacy_rate >= 50:
            return 'dotted'
        elif literacy_rate >= 30:
            return 'outline'
        else:
            return 'solid'
    
    def calculate_size(self, literacy_rate):
        """Calculate geometric shape size"""
        # Base size range: 0.3-1.0
        return 0.3 + (literacy_rate / 100) * 0.7
    
    def calculate_velocity(self, literacy_rate):
        """Calculate movement speed"""
        # Lower literacy rate = faster movement (symbolizing potential for change)
        base_speed = (100 - literacy_rate) / 100 * 2 + 0.5
        return {
            'x': np.random.uniform(-base_speed, base_speed),
            'y': np.random.uniform(-base_speed, base_speed)
        }
    
    def calculate_angular_velocity(self, literacy_rate):
        """Calculate angular velocity"""
        # High literacy rate shapes rotate more stably
        if literacy_rate >= 80:
            return np.random.uniform(-1, 1)
        else:
            return np.random.uniform(-3, 3)
    
    def map_literacy_to_hue(self, literacy_rate):
        """Map literacy rate to hue"""
        # Linear mapping from 0 degrees (red) to 240 degrees (blue)
        return literacy_rate / 100 * 240
    
    def map_literacy_to_hue_with_shape(self, literacy_rate, shape):
        """Map to hue based on shape and literacy rate, special shapes use dedicated color tones"""
        if shape == 'pentagon':
            # Pentagons use warm tones: red-orange-yellow range (0-60 degrees)
            return np.random.uniform(0, 60)
        elif shape == 'hexagon':
            # Hexagons use warm green tones: yellow-green to green range (60-120 degrees)
            return np.random.uniform(60, 120)
        else:
            # Other shapes maintain original hue mapping
            return literacy_rate / 100 * 240
    
    def calculate_saturation(self, literacy_rate):
        """Calculate saturation"""
        # Higher literacy rate = more vibrant
        return 0.4 + (literacy_rate / 100) * 0.6
    
    def calculate_lightness(self, literacy_rate):
        """Calculate lightness"""
        # Moderate lightness range
        return 0.3 + (literacy_rate / 100) * 0.4
    
    def calculate_opacity(self, literacy_rate):
        """Calculate transparency"""
        return 0.6 + (literacy_rate / 100) * 0.4
    
    def calculate_scale_factor(self, literacy_rate):
        """Calculate scale factor"""
        return 0.8 + (literacy_rate / 100) * 0.4
    
    def calculate_oscillation(self, literacy_rate):
        """Calculate oscillation amplitude"""
        # Lower literacy rate = larger oscillation
        return (100 - literacy_rate) / 100 * 0.1
    
    def calculate_frequency(self, literacy_rate):
        """Calculate oscillation frequency"""
        return 0.5 + (literacy_rate / 100) * 1.5
    
    def calculate_complexity(self, literacy_rate):
        """Calculate complexity level"""
        return min(10, max(1, int(literacy_rate / 10) + 1))
    
    def calculate_symmetry(self, literacy_rate):
        """Calculate symmetry order"""
        if literacy_rate >= 90:
            return 8  # Eight-fold symmetry
        elif literacy_rate >= 75:
            return 6  # Six-fold symmetry
        elif literacy_rate >= 60:
            return 4  # Four-fold symmetry
        elif literacy_rate >= 40:
            return 3  # Three-fold symmetry
        else:
            return 2  # Two-fold symmetry
    
    def get_edge_count(self, shape):
        """Get number of edges for shape"""
        edge_counts = {
            'circle': 0,
            'triangle': 3,
            'square': 4,
            'pentagon': 5,
            'hexagon': 6
        }
        return edge_counts.get(shape, 0)
    
    def generate_statistics(self, geometric_data):
        """Generate geometric statistics"""
        if not geometric_data:
            return {}
        
        # Shape distribution
        shape_counts = {}
        pattern_counts = {}
        literacy_rates = []
        
        for entity in geometric_data:
            shape = entity['shape']
            pattern = entity['pattern']
            literacy_rate = entity['literacy_rate']
            
            shape_counts[shape] = shape_counts.get(shape, 0) + 1
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            literacy_rates.append(literacy_rate)
        
        return {
            'total_entities': len(geometric_data),
            'shape_distribution': shape_counts,
            'pattern_distribution': pattern_counts,
            'literacy_statistics': {
                'mean': np.mean(literacy_rates),
                'median': np.median(literacy_rates),
                'std': np.std(literacy_rates),
                'min': min(literacy_rates),
                'max': max(literacy_rates)
            },
            'complexity_distribution': {
                'high_complexity': len([d for d in geometric_data if d['complexity_level'] >= 8]),
                'medium_complexity': len([d for d in geometric_data if 5 <= d['complexity_level'] < 8]),
                'low_complexity': len([d for d in geometric_data if d['complexity_level'] < 5])
            }
        }

def main():
    """Main function"""
    print("🔷 Starting Abstract Geometric Art Data Processor")
    
    processor = GeometricDataProcessor()
    data, stats = processor.process_literacy_data()
    
    if data:
        print(f"\n📊 Geometric Statistics:")
        print(f"Total entities: {stats['total_entities']}")
        print(f"Average literacy rate: {stats['literacy_statistics']['mean']:.1f}%")
        print(f"Literacy rate range: {stats['literacy_statistics']['min']:.1f}% - {stats['literacy_statistics']['max']:.1f}%")
        
        print(f"\n🔺 Shape distribution:")
        for shape, count in stats['shape_distribution'].items():
            print(f"  {shape}: {count}")
        
        print(f"\n🎨 Pattern distribution:")
        for pattern, count in stats['pattern_distribution'].items():
            print(f"  {pattern}: {count}")
    
    print("\n✅ Data processing completed, ready to generate geometric art!")

if __name__ == "__main__":
    main()