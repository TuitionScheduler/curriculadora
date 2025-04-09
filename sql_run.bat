@echo off
REM Batch file to populate the database (excluding Programs table)
REM Runs the scraper script for each term from 2005 to 2025.
REM Order is chronological (Spring, Summers, Fall) within each year,
REM starting with the earliest year.

@REM --- Year 2005 ---
echo Processing Year 2005...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2005 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2005 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2005 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2005 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2005 --no-ssh

@REM --- Year 2006 ---
echo Processing Year 2006...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2006 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2006 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2006 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2006 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2006 --no-ssh

@REM --- Year 2007 ---
echo Processing Year 2007...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2007 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2007 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2007 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2007 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2007 --no-ssh

@REM --- Year 2008 ---
echo Processing Year 2008...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2008 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2008 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2008 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2008 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2008 --no-ssh

@REM --- Year 2009 ---
echo Processing Year 2009...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2009 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2009 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2009 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2009 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2009 --no-ssh

@REM --- Year 2010 ---
echo Processing Year 2010...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2010 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2010 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2010 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2010 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2010 --no-ssh

@REM --- Year 2011 ---
echo Processing Year 2011...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2011 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2011 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2011 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2011 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2011 --no-ssh

@REM --- Year 2012 ---
echo Processing Year 2012...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2012 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2012 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2012 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2012 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2012 --no-ssh

@REM --- Year 2013 ---
echo Processing Year 2013...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2013 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2013 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2013 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2013 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2013 --no-ssh

@REM --- Year 2014 ---
echo Processing Year 2014...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2014 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2014 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2014 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2014 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2014 --no-ssh

@REM --- Year 2015 ---
echo Processing Year 2015...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2015 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2015 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2015 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2015 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2015 --no-ssh

@REM --- Year 2016 ---
echo Processing Year 2016...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2016 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2016 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2016 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2016 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2016 --no-ssh

@REM --- Year 2017 ---
echo Processing Year 2017...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2017 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2017 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2017 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2017 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2017 --no-ssh

@REM --- Year 2018 ---
echo Processing Year 2018...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2018 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2018 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2018 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2018 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2018 --no-ssh

@REM --- Year 2019 ---
echo Processing Year 2019...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2019 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2019 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2019 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2019 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2019 --no-ssh

@REM --- Year 2020 ---
echo Processing Year 2020...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2020 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2020 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2020 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2020 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2020 --no-ssh

@REM --- Year 2021 ---
echo Processing Year 2021...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2021 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2021 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2021 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2021 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2021 --no-ssh

@REM --- Year 2022 ---
echo Processing Year 2022...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2022 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2022 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2022 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2022 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2022 --no-ssh

@REM --- Year 2023 ---
echo Processing Year 2023...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2023 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2023 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2023 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2023 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2023 --no-ssh

@REM --- Year 2024 ---
echo Processing Year 2024...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2024 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2024 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2024 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2024 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2024 --no-ssh

@REM --- Year 2025 ---
echo Processing Year 2025...
poetry run python data/scraper/scrape_to_sql.py -t Spring -y 2025 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t FirstSummer -y 2025 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t SecondSummer -y 2025 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t ExtendedSummer -y 2025 --no-ssh
poetry run python data/scraper/scrape_to_sql.py -t Fall -y 2025 --no-ssh

echo All terms processed.

@REM Process course highest ancestor and difficulty.
echo Adding couse highest ancestor and difficulty.
poetry run python data/scraper/path_scraper.py
echo Course highest ancestor and difficulty processed.

@REM Add programs.
echo Adding program data.
poetry run python data/scraper/program_scraper.py
echo Program data processed.
