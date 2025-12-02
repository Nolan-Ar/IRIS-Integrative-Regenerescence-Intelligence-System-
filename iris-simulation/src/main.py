#!/usr/bin/env python3
"""
IRIS Economic Simulation - Command Line Interface

Usage:
    python main.py --agents 4069 --v_total 23530 --cycles 120

For help:
    python main.py --help
"""

import argparse
import yaml
import sys
from pathlib import Path
from datetime import datetime

from simulation import Simulation


def load_config(config_file: str = None) -> dict:
    """
    Load configuration from YAML file or use defaults

    Args:
        config_file: Path to config file (optional)

    Returns:
        Configuration dictionary
    """
    default_config = {
        'agents': 4069,
        'v_total': 23530,
        'cycles': 120,
        'entreprises_ratio': 0.3,
        'distribution': 'pareto_80_20',
        'seed': None,
        'output': None,
        'verbose': False,
        'generate_plots': True
    }

    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            file_config = yaml.safe_load(f)
            default_config.update(file_config)

    return default_config


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='IRIS Economic Simulation - Thermodynamic Economic System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default parameters
  python main.py

  # Custom simulation
  python main.py --agents 4069 --v_total 23530 --cycles 120

  # With specific seed for reproducibility
  python main.py --seed 42 --output data/runs/exp1

  # From config file
  python main.py --config config.yaml

For more information, see README.md
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to YAML configuration file'
    )

    parser.add_argument(
        '--agents',
        type=int,
        help='Number of initial agents (default: 4069)'
    )

    parser.add_argument(
        '--v_total',
        type=float,
        help='Total Verum to distribute (default: 23530)'
    )

    parser.add_argument(
        '--cycles',
        type=int,
        help='Number of simulation cycles (default: 120)'
    )

    parser.add_argument(
        '--entreprises_ratio',
        type=float,
        help='Proportion of agents with enterprises (default: 0.3)'
    )

    parser.add_argument(
        '--distribution',
        type=str,
        choices=['pareto_80_20', 'equal'],
        help='Initial wealth distribution (default: pareto_80_20)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducibility'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output directory for results'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Disable plot generation'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()

    # Load configuration
    config = load_config(args.config)

    # Override with command line arguments
    if args.agents is not None:
        config['agents'] = args.agents
    if args.v_total is not None:
        config['v_total'] = args.v_total
    if args.cycles is not None:
        config['cycles'] = args.cycles
    if args.entreprises_ratio is not None:
        config['entreprises_ratio'] = args.entreprises_ratio
    if args.distribution is not None:
        config['distribution'] = args.distribution
    if args.seed is not None:
        config['seed'] = args.seed
    if args.output is not None:
        config['output'] = args.output
    if args.verbose:
        config['verbose'] = True
    if args.no_plots:
        config['generate_plots'] = False

    # Display configuration
    print("\n" + "=" * 80)
    print("IRIS ECONOMIC SIMULATION")
    print("=" * 80)
    print("\nConfiguration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print("=" * 80)

    # Create and run simulation
    try:
        simulation = Simulation(config)
        simulation.run()

        # Generate statistical report if metrics available
        if simulation.metrics:
            from analysis.statistics import generate_full_report, save_report_txt

            df = simulation.metrics.to_dataframe()
            report = generate_full_report(df)

            # Save report
            output_dir = config.get('output')
            if not output_dir:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = f"data/runs/run_{timestamp}"

            report_path = Path(output_dir) / 'statistical_report.txt'
            save_report_txt(report, str(report_path))
            print(f"\n  ✓ Statistical report: {report_path}")

            # Print summary
            print("\n" + "=" * 80)
            print("SIMULATION RESULTS SUMMARY")
            print("=" * 80)
            print(f"\nThermodynamic Convergence:")
            print(f"  D/V final (12-cycle avg): {report['convergence']['last_12_mean']:.4f}")
            print(f"  Status: {report['convergence']['interpretation']}")
            print(f"\nInequality:")
            print(f"  {report['inequality']['interpretation']}")
            print(f"\nRegulation:")
            print(f"  {report['regulation']['interpretation']}")
            print(f"\nDemographics:")
            print(f"  {report['demographics']['interpretation']}")
            print("=" * 80)

        print(f"\n✓ Simulation completed successfully!")
        print(f"✓ Results saved to: {config.get('output', 'data/runs/')}")

    except KeyboardInterrupt:
        print("\n\n⚠ Simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error during simulation: {e}")
        if config.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
