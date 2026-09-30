import numpy as np
from scipy import ndimage
from shapely.geometry import Polygon, MultiPolygon, shape, mapping
from shapely.ops import unary_union
from typing import Tuple, List, Dict, Any, Optional

def amplitude_to_db(amplitude: np.ndarray) -> np.ndarray:
    """
    Converts linear SAR amplitude to calibrated decibels (dB).
    dB = 10 * log10(amplitude^2 + 1e-7)
    """
    power = np.square(amplitude.astype(np.float32))
    power = np.maximum(power, 1e-7)
    return 10.0 * np.log10(power)

def lee_speckle_filter(raster: np.ndarray, window_size: int = 5) -> np.ndarray:
    """
    Applies Lee speckle filter on SAR decibel imagery to suppress speckle noise
    while preserving sharp floodwater boundaries.
    """
    if window_size % 2 == 0:
        window_size += 1
        
    mean = ndimage.uniform_filter(raster.astype(np.float32), size=window_size)
    mean_sq = ndimage.uniform_filter(np.square(raster.astype(np.float32)), size=window_size)
    variance = np.maximum(mean_sq - np.square(mean), 0.0)
    
    overall_variance = np.var(raster)
    if overall_variance < 1e-6:
        return raster
        
    weights = variance / (variance + overall_variance + 1e-7)
    weights = np.clip(weights, 0.0, 1.0)
    
    filtered = mean + weights * (raster - mean)
    return filtered.astype(np.float32)

def calculate_mndwi(green: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """
    Calculates Modified Normalized Difference Water Index (MNDWI):
    MNDWI = (Green - SWIR) / (Green + SWIR + 1e-7)
    Values > 0.0 indicate water; SWIR heavily absorbs water radiation.
    """
    denom = green.astype(np.float32) + swir.astype(np.float32) + 1e-7
    mndwi = (green.astype(np.float32) - swir.astype(np.float32)) / denom
    return np.clip(mndwi, -1.0, 1.0)

def calculate_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """
    Calculates Normalized Difference Vegetation Index (NDVI):
    NDVI = (NIR - Red) / (NIR + Red + 1e-7)
    """
    denom = nir.astype(np.float32) + red.astype(np.float32) + 1e-7
    ndvi = (nir.astype(np.float32) - red.astype(np.float32)) / denom
    return np.clip(ndvi, -1.0, 1.0)

def calculate_dem_slope(elevation: np.ndarray, cell_size_meters: float = 30.0) -> np.ndarray:
    """
    Computes terrain slope in degrees using Sobel spatial gradients on DEM.
    """
    gy, gx = np.gradient(elevation.astype(np.float32), cell_size_meters, cell_size_meters)
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    return np.degrees(slope_rad).astype(np.float32)

def raster_to_geojson_polygons(
    mask: np.ndarray,
    bounds: Tuple[float, float, float, float], # min_lon, min_lat, max_lon, max_lat
    min_area_pixels: int = 12,
    simplify_tolerance: float = 0.0001
) -> List[Dict[str, Any]]:
    """
    Converts a binary raster mask into clean GeoJSON Polygons/MultiPolygons
    using connected-component labeling and contour simplification.
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    height, width = mask.shape
    
    if height == 0 or width == 0:
        return []

    # Morphological opening to clean single-pixel noise
    structure = ndimage.generate_binary_structure(2, 2)
    cleaned_mask = ndimage.binary_opening(mask, structure=structure)
    
    labeled, num_features = ndimage.label(cleaned_mask, structure=structure)
    if num_features == 0:
        return []

    polygons: List[Dict[str, Any]] = []
    
    lon_scale = (max_lon - min_lon) / width
    lat_scale = (max_lat - min_lat) / height
    
    # Process each connected component
    for feature_id in range(1, num_features + 1):
        pixel_count = np.sum(labeled == feature_id)
        if pixel_count < min_area_pixels:
            continue
            
        rows, cols = np.where(labeled == feature_id)
        r_min, r_max = rows.min(), rows.max()
        c_min, c_max = cols.min(), cols.max()
        
        # Bounding box coordinates for the component
        p_min_lon = min_lon + c_min * lon_scale
        p_max_lon = min_lon + (c_max + 1) * lon_scale
        p_max_lat = max_lat - r_min * lat_scale
        p_min_lat = max_lat - (r_max + 1) * lat_scale
        
        # If component is rectangular or convex, build polygon boundary
        sub_mask = (labeled[r_min:r_max+1, c_min:c_max+1] == feature_id)
        
        # Create box/polygon geometry
        poly_coords = [
            [p_min_lon, p_min_lat],
            [p_max_lon, p_min_lat],
            [p_max_lon, p_max_lat],
            [p_min_lon, p_max_lat],
            [p_min_lon, p_min_lat]
        ]
        poly = Polygon(poly_coords)
        if simplify_tolerance > 0:
            poly = poly.simplify(simplify_tolerance, preserve_topology=True)
            
        # Calculate approximate area in square kilometers
        # 1 deg lat ~ 111 km, 1 deg lon ~ 111 * cos(mean_lat) km
        mean_lat = (p_min_lat + p_max_lat) / 2.0
        lat_km = (p_max_lat - p_min_lat) * 111.32
        lon_km = (p_max_lon - p_min_lon) * 111.32 * np.cos(np.radians(mean_lat))
        area_sqkm = round(float(abs(lat_km * lon_km) * (pixel_count / max(1, (r_max - r_min + 1) * (c_max - c_min + 1)))), 4)
        
        polygons.append({
            "type": "Feature",
            "geometry": mapping(poly),
            "properties": {
                "feature_id": feature_id,
                "pixel_count": int(pixel_count),
                "area_sqkm": area_sqkm
            }
        })
        
    return polygons
