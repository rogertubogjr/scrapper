import json
from .services.agent_runner import run_agent_action
from .services.async_runner import run_async
from src.agent_helpers.property_keyword_scorer import property_keyword_scorer

def test():
  key_terms = [
    "individual rooms",
    "breakfast included",
    "max travel time 20m to site",
    "swimming pool",
    "avoid motorway hotels",
    "no travelodge",
  ]

  page_data = {
    "title": "Grand Hotel Central, Small Luxury Hotels",
    "location": "Via Laietana, 30, Ciutat Vella, 08003 Barcelona, Spain",
    "rating_reviews": "Scored 8.7 8.7Excellent 969 reviews",
    "room_info": "Grand Hotel Central, Small Luxury HotelsOpens in new windowCiutat Vella, BarcelonaShow on map0.7 km from downtownSubway AccessBeach Nearby1.4 km from beachSustainability certificationScored 8.7 8.7Excellent 969 reviewsLocation 9.6SuitePrivate suite2 beds (1 king, 1 sofa bed)Free stay for both childrenDaily spa access + high-speed internet 5 nights, 2 adults, 2 childrenUS$4,388Price US$4,388Additional charges may applySee availability",
    "price": "US$4,388",
    "page_data": {
        "property_description": "Grand Central Hotel Barcelona is a design hotel offering fantastic views of the Gothic Quarter and Barcelona Cathedral from its rooftop infinity pool. It has stylish rooms and free high-speed WiFi.\n\nThe elegantly refurbished hotel is housed in an early 20th-century building and it is a clear example of the Catalan Noucentisme.\n\nThe air-conditioned rooms at the Grand Hotel Barcelona have a modern design. They are equipped with a 4K high-definition TV´s with Chromecast . Each one has a bathroom with a large, rain-effect shower and luxury toiletries.\n\nThe restaurant offers an authentic Spanish-style dining experience with small \"platillos\" to be shared, as well as a selection of over 150 local and national wines. An excellent culinary proposal that will make you feel like a local. La Terraza del Central, in the rooftop, is the perfect place to enjoy a dinner, a cocktail or both overlooking the city lights of Barcelona.\n\nThe hotel has a fitness center and massage services are also offered. Staff at the 24-hour reception can provide information about what to see and do in Barcelona, and you can also hire a car or a bicycle.\n\nThe Born district, full of stylish shops and restaurants, is just 3 minutes’ walk from the Grand Central Hotel.",
        "facilities": [
            "Outdoor swimming pool",
            "Non-smoking rooms",
            "Room service",
            "Fitness center",
            "Facilities for disabled guests",
            "Spa",
            "Tea/Coffee Maker in All Rooms",
            "Bar",
            "Good Breakfast",
            "Free crib available on request",
            "Outdoor swimming pool",
            "Non-smoking rooms",
            "Room service",
            "Fitness center",
            "Facilities for disabled guests",
            "Spa",
            "Tea/Coffee Maker in All Rooms",
            "Bar",
            "Good Breakfast",
            "Free crib available on request"
        ],
        "info_prices": [
            {
                "room_type": "Superior Double\n1 king bed\n \n25 m²\nCity view\nAir conditioning\nAttached bathroom\nFlat-screen TV\nSoundproof\nCoffee machine\nMinibar\nFree Wifi\nFree toiletries\nBathrobe\nSafe\nStreaming service (like Netflix)\nToilet\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nInterconnecting room(s) available\nHeating\nHairdryer\nExtra long beds (> 6.5 ft)\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSingle-room AC for guest accommodation\nMore\nLess",
                "room_category": [
                    {
                        "occupancy": "+\nMax. people: 2\n<br>\nMax children: 2",
                        "payable": "₱ 120,594",
                        "conditions": [
                            {
                                "name": "Good breakfast ₱ 1,973"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n\n\n\nPay in advance"
                            },
                            {
                                "name": "No modifications"
                            },
                            {
                                "name": "Confirmed within 2 minutes"
                            },
                            {
                                "name": "Can't be combined with other offers"
                            },
                            {
                                "name": "Learn more"
                            },
                            {
                                "name": "We selected this option for you. You can only book one option with Partner Offer each time. Your previous selection is de-selected."
                            }
                        ]
                    }
                ]
            },
            {
                "room_type": "Suite\nRecommended for 2 adults, 2 children\nWe have 5 left\n1 king bed\nand\n1 sofa bed\nFree crib available on request\nPaneled throughout, with separate areas for relaxing and sleeping. A living room with sofa bed for 2, dining/working area as well as the luxury bathroom with shower and bathtub. Walk-in closet with triptych mirror. It includes a Nespresso coffee machine, two flat screen TVs, and Egyptian cotton sheets. The bathroom includes a shower, a bath and toiletries.\nPrivate suite56 m²City viewAir conditioningAttached bathroomFlat-screen TVSoundproofCoffee machineMinibarFree Wifi\nFree toiletries\nBathrobe\nSafe\nBidet\nStreaming service (like Netflix)\nToilet\nSofa\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nDesk\nSitting area\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nIroning facilities\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nHeating\nHairdryer\nExtra long beds (> 6.5 ft)\nWalk-in closet\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nDining area\nDining table\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSofa bed\nSingle-room AC for guest accommodation",
                "room_category": [
                    {
                        "occupancy": "+\nMax adults: 2\n<br>\nMax children: 2",
                        "payable": "₱ 254,892",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            },
                            {
                                "name": "Free stay for both children"
                            }
                        ]
                    },
                    {
                        "occupancy": "+\nMax adults: 2\n<br>\nMax children: 2",
                        "payable": "₱ 281,021",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            },
                            {
                                "name": "Free stay for both children"
                            }
                        ]
                    },
                    {
                        "occupancy": "+\nMax adults: 1\n<br>\nMax children: 2\nOnly for 1 guest",
                        "payable": "₱ 245,025",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            },
                            {
                                "name": "Free stay for both children"
                            }
                        ]
                    }
                ]
            },
            {
                "room_type": "Grand Suite\nWe have 1 left\n1 king bed\nand\n1 sofa bed\nFree crib available on request\nFeaturing a living and dining area , the suite has a a Nespresso coffee machine, two flat screen TVs with Chromecast media.\nPrivate suite70 m²Landmark viewCity viewAir conditioningAttached bathroomFlat-screen TVSoundproofCoffee machineMinibarFree Wifi\nFree toiletries\nBathrobe\nSafe\nAdditional bathroom\nBidet\nStreaming service (like Netflix)\nToilet\nSofa\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nDesk\nSitting area\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nIroning facilities\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nHeating\nHairdryer\nGuest bathroom\nExtra long beds (> 6.5 ft)\nWalk-in closet\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nDining area\nDining table\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSofa bed\nSingle-room AC for guest accommodation\nMore",
                "room_category": [
                    {
                        "occupancy": "+\nMax adults: 2\n<br>\nMax children: 2",
                        "payable": "₱ 319,193",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            },
                            {
                                "name": "Free stay for both children"
                            }
                        ]
                    },
                    {
                        "occupancy": "+\nMax adults: 3\n<br>\nMax children: 1",
                        "payable": "₱ 352,467",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 1, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            },
                            {
                                "name": "Free stay for 1 of your children (<1 years old)"
                            }
                        ]
                    },
                    {
                        "occupancy": "+\nMax adults: 1\n<br>\nMax children: 2\nOnly for 1 guest",
                        "payable": "₱ 309,327",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            },
                            {
                                "name": "Free stay for both children"
                            }
                        ]
                    }
                ]
            },
            {
                "room_type": "Superior Double\n1 king bed\nFree crib available on request\nThese rooms include a Nespresso coffee machine, a flat screen TV, and Egyptian cotton sheets. Lounge area to unwind with coffee table and armchairs. It includes a Nespresso coffee machine, a flat screen TV, and Egyptian cotton sheets.\n1 room25 m²City viewAir conditioningAttached bathroomFlat-screen TVSoundproofCoffee machineMinibarFree Wifi\nFree toiletries\nBathrobe\nSafe\nStreaming service (like Netflix)\nToilet\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nInterconnecting room(s) available\nHeating\nHairdryer\nExtra long beds (> 6.5 ft)\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSingle-room AC for guest accommodation\nMore",
                "room_category": [
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 129,827",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 144,253",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 149,560",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 163,985",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 139,694",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 154,119",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    }
                ]
            },
            {
                "room_type": "Superior Twin Room\n2 twin beds\nFree crib available on request\nProviding free toiletries and bathrobes, this twin room includes a private bathroom with a bath, a hairdryer and slippers. The air-conditioned twin room provides a flat-screen TV with streaming services, a private entrance, soundproof walls, a mini-bar as well as city views. The unit offers 2 beds.\n1 room25 m²City viewAir conditioningAttached bathroomFlat-screen TVSoundproofCoffee machineMinibarFree Wifi\nFree toiletries\nBathrobe\nSafe\nStreaming service (like Netflix)\nToilet\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nHeating\nHairdryer\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSingle-room AC for guest accommodation\nMore",
                "room_category": [
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 129,827",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 144,253",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 13, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 149,560",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 163,985",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 13, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 139,694",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 154,119",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 13, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    }
                ]
            },
            {
                "room_type": "Deluxe King Room\n1 king bed\nFree crib available on request\nOverlooking the Gothic Quarter and the ancient city wall, these rooms include a king-size bed.\n1 room28 m²City viewAir conditioningAttached bathroomFlat-screen TVSoundproofCoffee machineMinibarFree Wifi\nFree toiletries\nBathrobe\nSafe\nStreaming service (like Netflix)\nToilet\nSofa\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nHeating\nHairdryer\nExtra long beds (> 6.5 ft)\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSingle-room AC for guest accommodation\nMore",
                "room_category": [
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 145,443",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 161,604",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 165,176",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 181,337",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 155,310",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 171,470",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "discount may be available"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    }
                ]
            },
            {
                "room_type": "Deluxe Corner Room\nWe have 3 left\n1 king bed\nFree crib available on request\nWith a privileged location at the end of the building that gives it luminosity and exceptional panoramic views, these rooms include a king-size bed. It includes a Nespresso coffee machine, a flat screen TV with Chromecast media and Egyptian cotton sheets. The bathroom includes a shower, a bath and toiletries.\n1 room28 m²Landmark viewCity viewAir conditioningAttached bathroomFlat-screen TVSoundproofCoffee machineMinibarFree Wifi\nFree toiletries\nBathrobe\nSafe\nStreaming service (like Netflix)\nToilet\nSofa\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nHeating\nHairdryer\nExtra long beds (> 6.5 ft)\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSingle-room AC for guest accommodation\nMore",
                "room_category": [
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 160,447",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 178,275",
                        "conditions": [
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 180,180",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 198,007",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 170,313",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 188,141",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 10, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    }
                ]
            },
            {
                "room_type": "Junior Suite\nWe have 5 left\n1 king bed\nFree crib available on request\nOverlooking the ancient city walls, these rooms feature a seating area, and a king size bed.\nPrivate suite36 m²Landmark viewCity viewAir conditioningAttached bathroomFlat-screen TVSoundproofCoffee machineMinibarFree Wifi\nFree toiletries\nBathrobe\nSafe\nBidet\nStreaming service (like Netflix)\nToilet\nSofa\nBathtub or shower\nHardwood or parquet floors\nTowels\nLinens\nSocket near the bed\nHypoallergenic\nSitting area\nSuit press\nPrivate entrance\nTV\nSlippers\nTelephone\nIroning facilities\nSatellite channels\nTea/Coffee maker\nIron\nRadio\nHeating\nHairdryer\nExtra long beds (> 6.5 ft)\nWalk-in closet\nWake-up service/Alarm clock\nElectric kettle\nWake-up service\nLaptop safe\nWardrobe or closet\nDining area\nDining table\nUpper floors accessible by elevator\nToilet paper\nBoard games/puzzles\nSingle-room AC for guest accommodation\nMore",
                "room_category": [
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 223,354",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 2",
                        "payable": "₱ 245,978",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 13, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 213,487",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Non-refundable"
                            },
                            {
                                "name": "•\n                  Pay the property before arrival"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    },
                    {
                        "occupancy": "Max adults: 1\nOnly for 1 guest",
                        "payable": "₱ 236,112",
                        "conditions": [
                            {
                                "name": "Good breakfast included"
                            },
                            {
                                "name": "Includes daily spa access + high-speed internet"
                            },
                            {
                                "name": "Free cancellation before November 13, 2025"
                            },
                            {
                                "name": "No prepayment needed – pay at the property"
                            },
                            {
                                "name": "Enjoy a free private taxi from the airport to your accommodation. This offer is available for bookings up to 6 people and is provided and paid for by Booking.com. Cannot be combined with other offers, such as a Partner offer.\n\n\n\n\n\n\n\nFree private taxi from the airport to this property"
                            }
                        ]
                    }
                ]
            }
        ],
        "area_info": [
          {
              "category": "What's nearby",
              "areas": [
                  "European Museum of Modern Art250 m",
                  "Casa dels Canonges300 m",
                  "Picasso Museum300 m",
                  "Palau Berenguer Aguilar300 m",
                  "Plaça Sant Jaume350 m",
                  "Sant Felip Neri Square400 m",
                  "Memorial als caiguts el 1714450 m",
                  "Chocolate Museum550 m",
                  "Placa Reial750 m",
                  "Columnas del Templo de Augusto800 m"
              ]
          },
          {
              "category": "Restaurants & cafes",
              "areas": [
                  "RestaurantRestaurant Gloria7 m",
                  "RestaurantSapporo Ramen30 m",
                  "Cafe/BarStarbucks30 m"
              ]
          },
          {
              "category": "Top attractions",
              "areas": [
                  "Arc de Triomf850 m",
                  "Plaça Catalunya950 m",
                  "Barcelona Aquarium1.1 km",
                  "Barcelona Zoo1.2 km",
                  "Casa Batllo1.5 km",
                  "La Pedrera1.9 km",
                  "Agbar Tower2.7 km",
                  "Magic Fountain of Montjuic2.9 km",
                  "Montjuïc3.1 km",
                  "Park Güell4.2 km"
              ]
          },
          {
              "category": "Beaches in the Neighborhood",
              "areas": [
                  "Sant Miquel Beach1.7 km",
                  "Barceloneta Beach1.7 km",
                  "Somorrostro Beach1.7 km",
                  "Sant Sebastian Beach1.8 km",
                  "Nova Icaria Beach2.4 km"
              ]
          },
          {
              "category": "Public transit",
              "areas": [
                  "SubwayJaume I Metro Station100 m",
                  "SubwayUrquinaona Metro Station500 m",
                  "TrainEstació de França Train Station850 m",
                  "Buspl. de Catalunya - Bergara950 m",
                  "TrainArc de Triomf - Railway Station950 m",
                  "BusBarcelona (rda. Universitat, 33)1.1 km"
              ]
          },
          {
              "category": "Closest Airports",
              "areas": [
                  "Barcelona-El Prat Airport12 km",
                  "Girona-Costa Brava Airport94 km"
              ]
          }
        ]
    }
  }

  input_data = json.dumps(
    {
      "property_payload": page_data,
      "key_terms": key_terms,
    },
    ensure_ascii=False,
  )

  return run_async(run_agent_action(input_data, property_keyword_scorer, None, False))
