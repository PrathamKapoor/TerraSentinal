import numpy as np
from scipy import ndimage
from shapely.geometry import Polygon, MultiPolygon, shape, mapping, box, Point
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
    Computes terrain slope in degrees using Sobel spatial gradients on DEM with physical cell size.
    """
    gy, gx = np.gradient(elevation.astype(np.float32), cell_size_meters, cell_size_meters)
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    return np.degrees(slope_rad).astype(np.float32)

def raster_to_geojson_polygons(
    mask: np.ndarray,
    bounds: Tuple[float, float, float, float], # min_lon, min_lat, max_lon, max_lat
    min_area_pixels: int = 8,
    simplify_tolerance: float = 0.0004
) -> List[Dict[str, Any]]:
    """
    Converts a binary raster mask into clean GeoJSON Polygons/MultiPolygons
    using horizontal pixel run aggregation and unary union for exact spatial contours.
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
        pixel_count = int(np.sum(labeled == feature_id))
        if pixel_count < min_area_pixels:
            continue
            
        rows, cols = np.where(labeled == feature_id)
        r_min, r_max = int(rows.min()), int(rows.max())
        c_min, c_max = int(cols.min()), int(cols.max())
        
        # Aggregate horizontal runs of pixels to form exact polygonal boxes
        boxes = []
        for r in range(r_min, r_max + 1):
            row_mask = (labeled[r, c_min:c_max + 1] == feature_id)
            if not np.any(row_mask):
                continue
            
            # Find contiguous runs
            diff = np.diff(np.pad(row_mask.astype(np.int8), (1, 1), 'constant'))
            starts = np.where(diff == 1)[0]
            ends = np.where(diff == -1)[0]
            
            y_top = max_lat - r * lat_scale
            y_bot = max_lat - (r + 1) * lat_scale
            
            for s, e in zip(starts, ends):
                x_left = min_lon + (c_min + s) * lon_scale
                x_right = min_lon + (c_min + e) * lon_scale
                boxes.append(box(x_left, y_bot, x_right, y_top))
                
        if not boxes:
            continue
            
        # Merge runs into unified exact contour
        geom = unary_union(boxes)
        if simplify_tolerance > 0:
            geom = geom.simplify(simplify_tolerance, preserve_topology=True)
            
        if geom.is_empty:
            continue
            
        # Calculate real geographic area in square kilometers
        mean_lat = (min_lat + max_lat) / 2.0
        deg_lat_km = 111.32
        deg_lon_km = 111.32 * np.cos(np.radians(mean_lat))
        area_sqkm = round(float(geom.area * deg_lat_km * deg_lon_km), 3)
        
        polygons.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {
                "feature_id": feature_id,
                "pixel_count": pixel_count,
                "area_sqkm": area_sqkm
            }
        })
        
    return polygons
