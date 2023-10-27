export type PriceWarning = {
  region: string;
  error: any;
}

/**
 * The data returned from the price endpoint
 */
export type PriceData = {
  /**
   * The cheapest region
   */
  region: string;

  /**
   * Price of the cheapest region
   */
  price: string;

  /**
   * Any warnings that happened while trying to find the cheapest region
   */
  warnings: PriceWarning[];
}