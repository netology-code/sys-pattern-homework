variable "env_name" { 
  type = string
  default = "production" 
  }

variable "empty" { 
  type = string
  default = "" 
  }

locals{
  test_list = ["develop", "staging", "production"]
}


#1. Часто используемые функции

#> join( ",", ["Hello ", "world ", "!" ] ) 

#> split( "_", "A_B_C_D" ) 

#> type("a")
#> type([1,2,3])

#> concat( [ 1,2,3 ], [ 4,5,6 ] )

#> type(tolist( [ 1,2,3 ]) )
#> type(tolist([true, false]))
#> type(tolist( [ true,2,3,"a" ]) )

#> merge( { "1": "A ","2": "B" }, { "3": "C", "4": "D" } )



#> coalesce("", var.empty, 1, "a")
#> coalesce("", var.empty, "a", 1)
#> coalesce("", var.empty)

#> contains(tolist(["q","w","e"]), "w")
#> contains(tolist(["q","e"]), "w")

#> try(local.test_list[2], "develop")
#> try(local.test_list[9], "develop")


#> abspath(path.module)
#> basename(abspath(path.module))


#2. Условные выражения


#> var.env_name == "production" ? 3 : 1
#> var.env_name == "develop" ? 0 : 1

#3. for

#> [ for a in  local.test_list : upper(a) ]
#> [for a in  local.test_list : upper(a) if a !="production"]

#4. templatefile
