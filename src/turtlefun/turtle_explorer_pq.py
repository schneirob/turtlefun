"""src/turtlefun/turtle_explorer.py"""

from configparser import ConfigParser
from loguru import logger
import os
from queue import Queue
from threading import Thread, enumerate
from time import sleep
from typing import Union, List, Tuple

from .turtle import Turtle

default_path = "./es_results"

queue_theta = None
thread_path = None
thread_iterations = None
iterations_factor = 5

def _euler_spiral_calculation_pq():
    """Calculate Euler Spiral and create report"""
    global queue_theta, thread_iterations, thread_path, iterations_factor

    while not queue_theta.empty():
        (pvalue, qvalue) = queue_theta.get()
        theta = pvalue / qvalue * 360.0
        
        theta_str = "{:0.8}".format(theta).split(".")
        pvalue_str = str(pvalue)
        qvalue_str = str(qvalue)
        path = os.path.join(thread_path, "p=" + pvalue_str)
        basename = "tf_" + "p=" + pvalue_str + "--q=" + qvalue_str + "--theta=" + "{:012.8f}".format(float(theta)).replace(".","_") + ".png"
        os.makedirs(path, exist_ok=True)
        
        logger.trace("Using path {} with basename {} for storage", path, basename)
        
        data_exists = False
        data_file = None
        
        for file in os.listdir(path):
            if file.endswith(".ini") and file.startswith(basename):
                logger.trace("Matching file file {} found", file)
                config = ConfigParser()
                config.read(os.path.join(path, file))
                
                if not round(config.getfloat("es_results", "theta"), 10) == round(theta, 10):
                    logger.debug("Theta does not match")
                    continue
                
                if  config.getint("es_results", "iterate") == int(thread_iterations) or \
                        config.getboolean("es_results", "origin_return"):
                        data_exists = True
                        data_file = file
                        break
                
        if data_exists:
            logger.warning("Skipping theta={} as data exists according to {}", theta, data_file)
        else:
            logger.info("Starting caclulation of euler spiral for theta={}", theta)

            ti = thread_iterations
            if ti is None:
                ti = 2 * qvalue * iterations_factor
            
            t = Turtle(draw=False)
            t.euler_spiral(theta, ti)
            scale = t.autoscale(0.01)
            
            logger.trace("Drawing scaled with scale={}", theta, scale)
            t = Turtle(draw=True, scale=scale)
            t.linewidth = max(min(int(scale), 10), 1)
            t.euler_spiral(theta, ti)
            
            t.save(basename, path)
            
            logger.success("Finish caclulation of euler spiral for theta={}", theta)

def explore_euler_spiral_pq(p:List[int], q:List[int], iterations:Union[int, None], num_threads:int, path:Union[None, str] = None) -> None:
    """Explore the Euler spiral in a given p, q values

    For all combinations of p and q values theta = p / q * 360 ist explored
    
    Args:
        p ([int]): List of p values
        q ([int]): list of q values
        iterations (int): Number of iterations per euler spiral
        path (str, None): path to store results.
        num_threads (int): number of threads to start
    """
    pq = []
    for pvalue in p:
        for qvalue in q:
            pq.append((pvalue, qvalue))
    explore_euler_spiral_pq_list(pq, iterations, num_threads, path)

def explore_euler_spiral_pq_list(pq:List[Tuple[int, int]], iterations:Union[int, None], num_threads:int, path:Union[None, str] = None) -> None:
    """Explore the Euler spiral in a given p, q values

    For all combinations of p and q values theta = p / q * 360 ist explored
    
    Args:
        p ([(int, int)]): List of (p, q) values
        iterations (int): Number of iterations per euler spiral
        path (str, None): path to store results.
        num_threads (int): number of threads to start
    """
    global queue_theta, thread_path, thread_iterations, default_path
    
    thread_iterations = iterations
    
    if path is None:
        path = default_path
        
    logger.debug("Writing euler sprial exploration results to {}", path)
    
    if os.path.isdir(path):
        logger.warning("Path {} allready exists! Reusing existing files.", path)
    else:
        os.makedirs(path)
        logger.debug("Logging path {} newly created", path)
        
    thread_path = path
    
    queue_theta = Queue()
    for pvalue, qvalue in pq:

        queue_theta.put((pvalue, qvalue))
        logger.debug("Created queue entry for p={}, q={}", pvalue, qvalue)
        
    threads = []
    for _t in range(num_threads):
        threads.append(Thread(target=_euler_spiral_calculation_pq))
        
    for thread in threads:
        thread.start()
        
    while not queue_theta.empty():
        try:
            sleep(1)
        except KeyboardInterrupt:
            logger.warning("Exploration interrupted, but not finished. {} explorations remaining.", queue_theta.qsize())
            queue_theta = Queue()
            
    logger.debug("Waiting for threads to finish")
    
    while True:
        if len(enumerate()) > 1:
            logger.debug("{} remaining threads found. Waiting.", len(enumerate()) - 1)
            sleep(1)
        else:
            break

    logger.debug("Clean exit. Exloration finished.")