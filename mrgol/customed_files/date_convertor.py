#mabna dar in converotr tarikh: 1201/1/1 shamsi moadele : 1822/3/21 miladi mibashad. daghigh tar joloie esme har kelas convertor  ghofte shode ast.
def get_month_name(m):                   #m is month number (shamsi), this method is public method(can be used out of this file)
    return {1: 'فروردين', 2: 'ارديبهشت', 3: 'خرداد', 4: 'تير', 5: 'مرداد', 6: 'شهريور', 7: 'مهر', 8: 'آبان', 9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند'}[m]


def _shamsi_kabiseyears_list(years):                #list all kabise years between  1201/1/1 to ...    1201 is kabise but dont listed because one day reduced buy its first day.
    if years >= 1210:
        kabise_years = [1205, 1210]
        i = 1210
        nomral_kabise_conter = 0
        unusual_kabise_conter = 0
        while(i<years):
            nomral_kabise_conter += 1
            unusual_kabise_conter += 1
            i += 1
            if nomral_kabise_conter == 4:
                kabise_years += [i]
                nomral_kabise_conter = 0
            if unusual_kabise_conter == 28:
                i += 5
                kabise_years += [i]
                nomral_kabise_conter = 0
                unusual_kabise_conter = 0
        return kabise_years
    elif years >= 1205:
        return [1205]
    else:
        return []


def _miladi_kabiseyear_finder(year):                
    kabise_years = []
    if year%4 == 0:
        if year % 100 != 0 or year % 400 == 0:
            return True
        else:
            return False
    else:
        return False





class MiladiToShamsi:
    def __init__(self, y, m, d):                                            #you can import year from 1823/1/1 to ... (but years and days count from 1822/3/21)
        self.y = y
        self.m = m
        self.d = d

    def miladi_days(self):
        kabise_list = []
        if self.y-1 >= 1824:
            for y in range(1824, self.y):
                if _miladi_kabiseyear_finder(y):
                    kabise_list += [y]
                else:
                    pass
        else:
            kabise_list = []
        kabise_years = len(kabise_list)
        normal_years = self.y - 1 - 1822 - kabise_years
        days_before_currentyear = normal_years*365 + kabise_years*366
        days_currentyear = self.miladi_days_currentyear(_miladi_kabiseyear_finder(self.y))
        return days_before_currentyear + days_currentyear + 285

    def miladi_days_currentyear(self, kabise):
        j=0
        days = 0
        miladi_months_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] if kabise else [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        miladi_months_days = miladi_months_days[:self.m-1]
        for month_days in miladi_months_days:                          #we dont want last month here.
            days += month_days
        days = days + self.d
        return days
    
    def shamsi_month_day(self, days, kabise):
        shamsi_months_days = [31]*6 + [30]*6
        if days == 0:
            month_day = [12, 30] if kabise else [12, 29]
            return month_day        
        if days <=31:
            return [1, days]
        months_days = 0
        for i in range(len(shamsi_months_days)-1):
            months_days += shamsi_months_days[i]
            if days <= months_days+shamsi_months_days[i+1]:
                return [int(i+2), int(days-months_days)]
  
    def result(self, month_name=False):
        miladi_days = self.miladi_days()                   
        current_year = 1201
        miladi_days2 = 0
        miladi_days3 = 0
        if miladi_days <= 365:
            date = [1201, *self.shamsi_month_day(miladi_days+1, True)]  
        else:
            while(True):
                kabise = True if current_year in _shamsi_kabiseyears_list(current_year) else False                
                miladi_days2 += 366 if kabise else 365
                if miladi_days2 >= miladi_days:
                    miladi_days2 -= 366 if kabise else 365
                    miladi_days3 = miladi_days - miladi_days2
                    break
                current_year += 1
            kabise = True if current_year in _shamsi_kabiseyears_list(current_year) else False   
            real_year = current_year
            date = [real_year, *self.shamsi_month_day(miladi_days3, kabise)]
        if not month_name:
            return date                                                                  #this is like [1398, 6, 15]
        else:
            date[1] = get_month_name(date[1])
            return date                                                                  #this is like [1398, 'mer', 15]     mer in persian!




        
class ShamsiToMiladi:
    def __init__(self, y, m, d):                                            #you can import year from 1202/1/1 to ... (but years and days count from 1201/1/1)
        self.y = y
        self.m = m
        self.d = d

    def shamsi_days(self):
        kabise_list = _shamsi_kabiseyears_list(self.y-1)
        kabise_years = len(kabise_list)
        normal_years = self.y - 1 - 1200 - kabise_years
        days_before_currentyear = normal_years*365 + kabise_years*366
        days_currentyear = self.shamsi_days_currentyear()
        return days_before_currentyear + days_currentyear

    def shamsi_days_currentyear(self):
        j=0
        days = 0
        for i in range(self.m-1):                          #we dont want last month here.
            j += 1
            if j < 7:
                days += 31
            elif j < 12:
                days += 30
            else:
                pass
        days = days + self.d
        return days
    
    def miladi_month_day(self, days, kabise):
        miladi_months_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] if kabise else [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if days == 0:
            return [12, 31]
        if days <=31:
            return [1, days]
        months_days = 0
        for i in range(len(miladi_months_days)-1):
            months_days += miladi_months_days[i]
            if days <= months_days+miladi_months_days[i+1]:
                return [int(i+2), int(days-months_days)]
            
    def result(self):
        shamsi_days = self.shamsi_days()                   
        shamsi_days -= 285
        shamsi_days2 = 0
        shamsi_days3 = 0
        current_year = 1823
        if shamsi_days < 365:
            return [1823, *self.miladi_month_day(shamsi_days, False)]
        else:
            while(True):
                kabise = True if _miladi_kabiseyear_finder(current_year) else False
                shamsi_days2 += 366 if kabise else 365
                if shamsi_days2 >= shamsi_days:
                    shamsi_days2 -= 366 if kabise else 365
                    shamsi_days3 = shamsi_days - shamsi_days2
                    break
                current_year += 1
            real_year = current_year 
            return [real_year, *self.miladi_month_day(shamsi_days3, _miladi_kabiseyear_finder(real_year))]


