# Scientific references

The PDFs in `scientific/` are immutable external source material. Filenames are preserved exactly as supplied. Hashes identify the repository files; a matching title or citation alone does not establish byte identity with another copy.

| Exact filename | SHA-256 | Broad role/purpose | Documented provenance/status |
| --- | --- | --- | --- |
| `1979-Influence_of_gravity_wave_activity_on_lower_thermospheric_photochemistry_and_composition.pdf` | `075858df67be318bb098ce82b55d48452e3ebfb02c5425e6224d7a8dedfaeaac` | Gravity-wave photochemistry context | Supporting historical context for the legacy application |
| `1983-Ozone_density_distribution_in_the_mesosphere_(50-90_km)_measured_by_the_SME_limb_scanning_near_infrared_spectromete.pdf` | `92610019f3449ba1c576a04cd19857316bd71dc2809f5946d9adad93500f6f54` | SME mesospheric ozone observations | Supporting observational context |
| `1984-The_Vertical_Distribution_of_Ozone_in_the_Mesosphere_and_Lower_Thermosphere (1).pdf` | `0f4442f486a1f5e6f02448c651577ba162fd0eb842a9f4f7f46a8bbe50779e96` | Mesospheric HOx/ozone validation | Supporting source for later validation |
| `1993.pdf` | `d303f1e849496a54306f5c2550e942cd1ba592043ad302a991b1d5aec1c00e97` | Airglow-mechanism validation | Mlynczak, Solomon, and Zaras (1993), identified by the accepted source inventory; supporting source for later validation |
| `2006JD008355.pdf` | `7abba68719c351609c514608dc00ab0dcf53259baed704367b4147b7cfe45dbc` | SABER daytime O2(1Delta)/ozone work | Supporting observational/model-validation source |
| `Aeronomy of the Middle Atmosphere_ Chemistry and Physics of the Stratosphere and Mesosphere.pdf` | `e43cd39b21d4f3d4c401ceddbe72da8801443db3bffdcb600374304dda61ca22` | Barth chemistry, SOCRATES profiles, and O2 channel identities | Brasseur and Solomon (2005); primary/historical baseline source used by M4A and M4B; hash matches accepted documentation |
| `JPL_Publication_15-10_compressed.pdf` | `a5c57b2a8435760bc4dd43da328a9dd34768865c022e965326f3eccaaf0cd3c8` | JPL Evaluation 18 reference material | File identity does not match the JPL18 hashes recorded for other source copies in the accepted package; do not infer equivalence from the title |
| `Journal of Geophysical Research  Atmospheres - 2007 - Zhu - Effect of dynamical‐photochemical coupling on oxygen airglow.pdf` | `c371eb9c4e5d49664472a3ba76a4a6c02c452e315a1cc85cb432c3bcba1aa2d1` | Dynamical-photochemical coupling | Supporting interpretation and validation source |
| `NASA_Data_Evaluation_20.pdf` | `835496c8fd180b29ff9fc456e038dc8fd34e829e5f6e00346b0837ad71b4169c` | JPL Evaluation 20 | Corroborative material only for `historical_2020`; not an automatic numerical replacement; hash matches accepted M4C metadata |
| `anqi2020.pdf` | `3bf92a0c36147e9c4f3d200ec3e37c2cbdf61143470cbd6c61f6075d98824df5` | Ozone/airglow retrieval, reaction topology, and atmospheric assumptions | Li et al. (2020); primary/historical baseline source used in M2 and M4A; hash matches accepted documentation |
| `anqisthesis.pdf` | `c4b2e0e85ed4fc7abf641991389c76c3c4fe82c9030d786e0e42139d36cec38c` | Legacy executable specification and photolysis partition context | Anqi Li MSc thesis (2017); primary legacy source used by M1 and M4B |
| `koppers&murtagh.pdf` | `0d89cd56bfd5e16e25560fe2aaea7be9f47857d8c9647683f7a5a7d7f67175eb` | Schumann-Runge parameterization | Koppers and Murtagh (1996), identified by the accepted source inventory; supporting historical-radiation source |
| `murtaghSR.pdf` | `7c76727641a1cb4f7407471b8d1cb91fbd0313cb3b74cd5bebfa58299b6654f6` | Schumann-Runge cross sections | Murtagh (1989), identified by the accepted source inventory; supporting historical-radiation source |

`NASA_Data_Evaluation_20.pdf` must not be used to replace an exact historical baseline source silently. M4D is **NOT IMPLEMENTED / DESIGN NOT FROZEN**; historical O2 spectroscopy, including HITRAN2016/TIPS2017 provenance, remains an unresolved source/provenance risk for the independent M4D design. If the required historical data cannot be verified, the project must stop with **SOURCE BLOCKER** rather than substitute modern data silently.
