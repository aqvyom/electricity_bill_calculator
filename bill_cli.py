import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO)

# Enum for connection categories
class ConnectionCategory(Enum):
    DS1D = 'DS1D'
    DS2D = 'DS2D'

    @staticmethod
    def is_valid(value: str) -> bool:
        return value in ConnectionCategory.__members__

# Dataclass for storing rate configuration
@dataclass
class RateConfig:
    rate_under_limit: float
    rate_over_limit: float
    subsidy_under_limit: float
    subsidy_over_limit: float
    fixed_charge: float  # per kW
    limit: float  # monthly consumption limit

# Fixed rates for different connection categories
class RateConstants(Enum):
    DS1D = RateConfig(7.42, 8.95, 4.97, 5.11, 40, 50)
    DS2D = RateConfig(7.42, 7.96, 3.30, 3.43, 80, 100)

# Bill Calculator class
class BillCalculator:
    def __init__(self, category: Optional[str] = None, units: Optional[float] = None,
                 days: Optional[int] = None, load_input: Optional[str] = None,
                 previous_due: Optional[float] = None):
        self.category = ConnectionCategory.DS2D
        self.units = units
        self.days = days
        self.load_input = load_input
        self.previous_due = previous_due

        if category and ConnectionCategory.is_valid(category):
            self.category = ConnectionCategory[category]
        elif category:
            print("Invalid category! Defaulting to DS2D.")

    def parse_load(self, load_input: str) -> Tuple[int, int]:
        try:
            # Match all numbers in the input string
            values = list(map(int, re.findall(r'\d+', load_input)))
            if len(values) != 2:
                raise ValueError
            demanded_load = min(values)
            total_load = max(values)
            return total_load, demanded_load
        except ValueError:
            print("Invalid load input. Defaulting total and demanded load to 1.")
            return 1, 1

    def calculate_bill(self):
        if None in (self.units, self.days, self.load_input, self.previous_due):
            raise ValueError("Missing input values for calculation")

        total_load, demanded_load = self.parse_load(self.load_input)
        config = RateConstants[self.category.value].value
        adjusted_units = (self.units / self.days) * 30

        energy_amount, subsidy_amount = self.calculate_energy_and_subsidy(adjusted_units, self.days, config)
        fixed_charges = self.calculate_fixed_charges(demanded_load, self.days, config)
        excess_load_surcharge = self.calculate_excess_load_surcharge(total_load, demanded_load, config, self.days)
        delayed_payment_surcharge = self.calculate_dps(self.previous_due)
        electricity_duty = self.calculate_electricity_duty(energy_amount)

        net_bill_after_subsidy = energy_amount - subsidy_amount
        total_due = net_bill_after_subsidy + fixed_charges + electricity_duty + delayed_payment_surcharge + excess_load_surcharge
        final_amount_due = total_due + self.previous_due

        self.display_output(energy_amount, subsidy_amount, net_bill_after_subsidy,
                            delayed_payment_surcharge, fixed_charges,
                            excess_load_surcharge, electricity_duty,
                            total_due, self.previous_due, final_amount_due)

    def calculate_energy_and_subsidy(self, adjusted_units, days, config):
        if adjusted_units <= config.limit:
            energy = adjusted_units * config.rate_under_limit * (days / 30)
            subsidy = adjusted_units * config.subsidy_under_limit * (days / 30)
        else:
            energy = (config.limit * config.rate_under_limit + (adjusted_units - config.limit) * config.rate_over_limit) * (days / 30)
            subsidy = (config.limit * config.subsidy_under_limit + (adjusted_units - config.limit) * config.subsidy_over_limit) * (days / 30)
        return energy, subsidy

    def calculate_fixed_charges(self, demanded_load, days, config):
        return demanded_load * config.fixed_charge * (days / 30)

    def calculate_excess_load_surcharge(self, total_load, demanded_load, config, days):
        excess_load = total_load - demanded_load
        if excess_load > 0:
            return config.fixed_charge * excess_load * 2 * (days / 30)
        return 0

    def calculate_dps(self, previous_due):
        return previous_due * 0.015 if previous_due > 0 else 0

    def calculate_electricity_duty(self, energy_amount):
        return energy_amount * 0.06

    def display_output(self, energy, subsidy, net_bill, dps, fixed, excess, duty, total, prev_due, final):
        print(f"\n--- Electricity Bill Details ---")
        print(f"Energy Consumption Amount : ₹{energy:.2f}")
        print(f"Subsidy Amount            : ₹{subsidy:.2f}")
        print(f"Net Bill After Subsidy    : ₹{net_bill:.2f}")
        print(f"Delayed Payment Surcharge : ₹{dps:.2f}")
        print(f"Fixed Charges             : ₹{fixed:.2f}")
        print(f"Excess Load Surcharge     : ₹{excess:.2f}")
        print(f"Electricity Duty          : ₹{duty:.2f}")
        print(f"Total Due (excl. prev due): ₹{total:.2f}")
        print(f"Previous Due              : ₹{prev_due:.2f}")
        print(f"Final Amount Due          : ₹{final:.2f}")

# Optional CLI interface for manual input
def run_cli():
    try:
        category_input = input("Enter Connection Category (DS1D / DS2D): ").strip()
        units = float(input("Enter the number of units consumed: "))
        days = int(input("Enter the number of days: "))
        load_input = input("Enter Total Load (TL, DL): ").strip()
        previous_due = float(input("Enter previous due amount: "))

        calc = BillCalculator(category_input, units, days, load_input, previous_due)
        calc.calculate_bill()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_cli()