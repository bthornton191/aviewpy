from math import pi
import unittest
from pathlib import Path

import pygmsh

from aviewpy.files.shell import get_shell_volume, plot_shell, read_shell_file, write_shell_file

TEST_CUBE_FILE = Path(__file__).parent / 'resources' / 'box.shl'
TEST_HELICAL_TOOTH_FILE = Path(__file__).parent / 'resources' / 'helical_tooth.shl'
TEST_HELICAL_TOOTH_VOLUME = 8.8328859429E-03
TEST_WORN_HELICAL_TOOTH_FILE = Path(__file__).parent / 'resources' / 'worn_helical_tooth.shl'
TEST_WORN_HELICAL_TOOTH_VOLUME = 8.6114625014E-03
TEST_LEADSCREW_FILE = Path(__file__).parent / 'resources' / 'leadscrew.shl'
TEST_WORN_LEADSCREW_FILE = Path(__file__).parent / 'resources' / 'worn_leadscrew.shl'
TEST_WORN_LEADSCREW_VOLUME = 29.4121024398
TEST_CUBE_LENGTH = 2
TEST_L_N_CUBES = 5

class Test_ShellVolume(unittest.TestCase):
    """Tests the get_shell_volume function"""

    def test_returns_correct_volume_for_cube(self):
        """Tests that get_shell_volume returns the correct volume for a cube"""
        points, facets = make_cube_shell(TEST_CUBE_LENGTH)
        volume = get_shell_volume(points, facets)
        expected_volume = TEST_CUBE_LENGTH**3
        self.assertAlmostEqual(volume, expected_volume)

    def test_returns_correct_volume_for_extruded_L_shape(self):
        """Tests that get_shell_volume returns the correct volume for a cube"""
        points, facets = make_L_shell(TEST_CUBE_LENGTH)
        volume = get_shell_volume(points, facets)
        total_cubes = (TEST_L_N_CUBES-1)*2 + 1
        cube_volume = (TEST_CUBE_LENGTH**3)
        expected_volume = cube_volume*total_cubes
        self.assertAlmostEqual(volume, expected_volume)

    def test_returns_correct_volume_for_pipe(self):
        """Tests that get_shell_volume returns the correct volume for a cube"""
        L_pipe = 5
        od_pipe = 1
        id_pipe = .75
        points, facets = make_pipe(od_pipe, id_pipe, L_pipe, .05)
        volume = get_shell_volume(points, facets)
        expected_volume = pi/4*(od_pipe**2 - id_pipe**2)*L_pipe
        self.assertAlmostEqual(volume, expected_volume, 3)

    def test_returns_correct_volume_for_helical_tooth(self):
        """Tests that get_shell_volume returns the correct volume for a helical tooth"""
        points, facets = read_shell_file(TEST_HELICAL_TOOTH_FILE)
        volume = get_shell_volume(points, facets)
        expected_volume = TEST_HELICAL_TOOTH_VOLUME
        self.assertAlmostEqual(volume, expected_volume, places=4)

    def test_returns_correct_volume_for_worn_helical_tooth(self):
        """Tests that get_shell_volume returns the correct volume for a helical tooth"""
        points, facets = read_shell_file(TEST_WORN_HELICAL_TOOTH_FILE)
        volume = get_shell_volume(points, facets)
        expected_volume = TEST_WORN_HELICAL_TOOTH_VOLUME
        self.assertAlmostEqual(volume, expected_volume, places=3)

    def test_returns_correct_volume_for_leadscrew(self):
        """Tests that get_shell_volume returns the correct volume for a helical tooth"""
        points, facets = read_shell_file(TEST_LEADSCREW_FILE)
        volume = get_shell_volume(points, facets)
        expected_volume = 29
        self.assertAlmostEqual(volume, expected_volume, places=0)

    def test_returns_correct_volume_for_worn_leadscrew(self):
        """Tests that get_shell_volume returns the correct volume for a helical tooth"""
        points, facets = read_shell_file(TEST_WORN_LEADSCREW_FILE)
        volume = get_shell_volume(points, facets)
        expected_volume = TEST_WORN_LEADSCREW_VOLUME
        self.assertAlmostEqual(volume, expected_volume, places=3)

    # @unittest.skip('Plotting tests are only for visual inspection')
    def test_plot_shell(self):
        """Tests that get_shell_volume returns the correct volume for a cube"""
        points, facets = make_pipe(1, .75, 5)
        ax = plot_shell(points, facets)
        self.assertTrue(ax)


def make_cube_shell(edge_length):
    """Make a cube shell"""
    with pygmsh.geo.Geometry() as geom:
        geom.add_box(0,edge_length ,0,edge_length ,0,edge_length , mesh_size=0.5)
        mesh = geom.generate_mesh()

    points = mesh.points
    facets = mesh.cells[1].data

    return points, facets

def make_L_shell(edge_length, n_cubes=5, mesh_size = 0.5):
    """Make a L shell by stacking `n_cubes` cubes"""
    with pygmsh.geo.Geometry() as geom:
        poly = geom.add_polygon(
            [
                [0, 0, 0],
                [edge_length*n_cubes, 0, 0],
                [edge_length*n_cubes, edge_length, 0],
                [edge_length, edge_length, 0],
                [edge_length, edge_length*n_cubes, 0],
                [0, edge_length*n_cubes, 0]
            ],
            mesh_size=mesh_size)
        geom.extrude(poly, [0.0, 0, edge_length], num_layers=2)
        mesh = geom.generate_mesh()

    points = mesh.points
    facets = mesh.cells[1].data

    return points, facets

def make_pipe(od, id, length, mesh_size = 0.1):
    with pygmsh.occ.Geometry() as geom:
        geom.characteristic_length_max = mesh_size
        outer_cyl=geom.add_cylinder([0, 0.0, 0], [0.0, 0.0, length], od/2)
        inner_cyl=geom.add_cylinder([0, 0.0, 0], [0.0, 0.0, length], id/2)
        geom.boolean_difference(outer_cyl, inner_cyl)

        mesh = geom.generate_mesh()

    points = mesh.points
    facets = mesh.cells[1].data

    return points, facets